from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOL = ROOT / '.agents/tools/template-sync.py'


def run(command: list[str], cwd: Path, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if check and result.returncode != 0:
        raise AssertionError(f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}")
    return result


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return run(['git', *args], root, check=check)


def write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')


def init_repo(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    git(root, 'init', '-b', 'main')
    git(root, 'config', 'user.name', 'Test User')
    git(root, 'config', 'user.email', 'test@example.com')


def commit_all(root: Path, message: str) -> str:
    git(root, 'add', '-A')
    git(root, 'commit', '-m', message)
    return git(root, 'rev-parse', 'HEAD').stdout.strip()


def config(upstream: Path, baseline: str | None) -> str:
    return json.dumps(
        {
            'schema_version': 'paper-template-sync-v1',
            'upstream': {
                'url': str(upstream),
                'remote': 'template',
                'branch': 'main',
            },
            'last_synced_commit': baseline,
            'always_manual': [],
            'ignored_paths': [],
        },
        indent=2,
    ) + '\n'


def skill() -> str:
    return '# Skill\n\n## Trigger\nX\n\n## Minimum context\nX\n\n## Procedure\nX\n\n## Safety boundary\nX\n'


class TemplateSyncTests(unittest.TestCase):

    def test_current_repository_configuration_passes(self) -> None:
        result = subprocess.run(
            [sys.executable, str(TOOL), "--root", str(ROOT), "validate"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.upstream = base / 'upstream'
        self.downstream = base / 'downstream'
        init_repo(self.upstream)
        write(self.upstream, '.agents/tools/base.txt', 'base-v1\n')
        write(self.upstream, '.agents/tools/conflict.txt', 'conflict-v1\n')
        write(self.upstream, 'PAPER.md', 'paper-v1\n')
        write(self.upstream, 'CONTRIBUTING.md', 'contributing-v1\n')
        write(self.upstream, 'PUBLICATION.md', 'publication-v1\n')
        self.baseline = commit_all(self.upstream, 'template v1')

        init_repo(self.downstream)
        shutil.copytree(self.upstream / '.agents', self.downstream / '.agents')
        shutil.copy2(self.upstream / 'PAPER.md', self.downstream / 'PAPER.md')
        shutil.copy2(self.upstream / 'CONTRIBUTING.md', self.downstream / 'CONTRIBUTING.md')
        shutil.copy2(self.upstream / 'PUBLICATION.md', self.downstream / 'PUBLICATION.md')
        write(self.downstream, '.agents/template-sync.json', config(self.upstream, self.baseline))
        write(self.downstream, '.agents/skills/template-sync/SKILL.md', skill())
        commit_all(self.downstream, 'paper from template v1')
        git(self.downstream, 'switch', '-c', 'chore/template-sync')
        git(self.downstream, 'remote', 'add', 'template', str(self.upstream))
        git(self.downstream, 'fetch', 'template', 'main')

        write(self.upstream, '.agents/tools/base.txt', 'base-v2\n')
        write(self.upstream, '.agents/tools/conflict.txt', 'conflict-upstream-v2\n')
        write(self.upstream, '.agents/tools/new.txt', 'new-v2\n')
        write(self.upstream, 'PAPER.md', 'paper-upstream-v2\n')
        write(self.upstream, 'CONTRIBUTING.md', 'contributing-upstream-v2\n')
        write(self.upstream, 'PUBLICATION.md', 'publication-upstream-v2\n')
        write(self.upstream, '.agents/tools/check-reference-integrity.py', 'sidecar checker\n')
        write(self.upstream, '.agents/dependencies/reference-integrity/uv.lock', 'locked dependency\n')
        write(self.upstream, '.github/workflows/reference-validation.yml', 'inert until policy enables it\n')
        write(self.upstream, 'REFERENCES.md', 'reference contract\n')
        write(self.upstream, 'references/ledger.json', '{}\n')
        self.target = commit_all(self.upstream, 'template v2')
        git(self.downstream, 'fetch', 'template', 'main')

        write(self.downstream, '.agents/tools/conflict.txt', 'conflict-downstream\n')
        commit_all(self.downstream, 'custom downstream tool')

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def tool(self, *args: str, check: bool = False) -> subprocess.CompletedProcess[str]:
        return run([sys.executable, str(TOOL), '--root', str(self.downstream), *args], self.downstream, check=check)

    def test_validate_and_plan_classification(self) -> None:
        validate = self.tool('validate')
        self.assertEqual(validate.returncode, 0, validate.stderr)
        plan = self.tool('plan')
        self.assertEqual(plan.returncode, 0, plan.stderr)
        data = json.loads((self.downstream / '.agents/runtime/template-sync/plan.json').read_text())
        by_path = {item['path']: item for item in data['items']}
        self.assertEqual(by_path['.agents/tools/base.txt']['category'], 'safe')
        self.assertEqual(by_path['.agents/tools/new.txt']['category'], 'safe')
        self.assertEqual(by_path['.agents/tools/conflict.txt']['category'], 'conflict')
        self.assertEqual(by_path['PAPER.md']['category'], 'manual')
        self.assertEqual(by_path['CONTRIBUTING.md']['category'], 'manual')
        self.assertEqual(by_path['PUBLICATION.md']['category'], 'manual')
        self.assertEqual(by_path['.agents/tools/check-reference-integrity.py']['category'], 'safe')
        self.assertEqual(by_path['.agents/dependencies/reference-integrity/uv.lock']['category'], 'manual')
        self.assertEqual(by_path['.github/workflows/reference-validation.yml']['category'], 'manual')
        self.assertEqual(by_path['REFERENCES.md']['category'], 'manual')
        self.assertEqual(by_path['references/ledger.json']['category'], 'manual')

    def test_apply_safe_and_export_review_bundle(self) -> None:
        plan = self.tool('plan')
        self.assertEqual(plan.returncode, 0, plan.stderr)
        applied = self.tool('apply')
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual((self.downstream / '.agents/tools/base.txt').read_text(), 'base-v2\n')
        self.assertEqual((self.downstream / '.agents/tools/new.txt').read_text(), 'new-v2\n')
        self.assertEqual((self.downstream / '.agents/tools/conflict.txt').read_text(), 'conflict-downstream\n')
        self.assertEqual((self.downstream / 'PAPER.md').read_text(), 'paper-v1\n')
        self.assertEqual((self.downstream / 'CONTRIBUTING.md').read_text(), 'contributing-v1\n')
        self.assertEqual((self.downstream / 'PUBLICATION.md').read_text(), 'publication-v1\n')
        self.assertEqual(
            (self.downstream / '.agents/tools/check-reference-integrity.py').read_text(),
            'sidecar checker\n',
        )
        self.assertFalse((self.downstream / '.agents/dependencies/reference-integrity/uv.lock').exists())
        self.assertFalse((self.downstream / '.github/workflows/reference-validation.yml').exists())
        self.assertFalse((self.downstream / 'REFERENCES.md').exists())
        self.assertFalse((self.downstream / 'references/ledger.json').exists())
        bundle = self.downstream / '.agents/runtime/template-sync/merge-bundle'
        self.assertEqual((bundle / 'upstream/PAPER.md').read_text(), 'paper-upstream-v2\n')
        self.assertEqual((bundle / 'baseline/PAPER.md').read_text(), 'paper-v1\n')
        self.assertEqual((bundle / 'upstream/CONTRIBUTING.md').read_text(), 'contributing-upstream-v2\n')
        self.assertEqual((bundle / 'baseline/CONTRIBUTING.md').read_text(), 'contributing-v1\n')
        self.assertEqual(
            (bundle / 'upstream/.github/workflows/reference-validation.yml').read_text(),
            'inert until policy enables it\n',
        )
        self.assertEqual((bundle / 'upstream/references/ledger.json').read_text(), '{}\n')

    def test_apply_refuses_default_branch_and_dirty_tree(self) -> None:
        self.tool('plan')
        git(self.downstream, 'switch', 'main')
        refused = self.tool('apply')
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('default branch', refused.stderr)
        git(self.downstream, 'switch', 'chore/template-sync')
        write(self.downstream, 'dirty.txt', 'dirty\n')
        refused_dirty = self.tool('apply')
        self.assertNotEqual(refused_dirty.returncode, 0)
        self.assertIn('dirty worktree', refused_dirty.stderr)

    def test_bootstrap_and_record(self) -> None:
        cfg_path = self.downstream / '.agents/template-sync.json'
        cfg = json.loads(cfg_path.read_text())
        cfg['last_synced_commit'] = None
        cfg_path.write_text(json.dumps(cfg, indent=2) + '\n')
        commit_all(self.downstream, 'remove baseline')
        no_bootstrap = self.tool('plan')
        self.assertNotEqual(no_bootstrap.returncode, 0)
        self.assertIn('--bootstrap', no_bootstrap.stderr)
        bootstrap = self.tool('plan', '--bootstrap')
        self.assertEqual(bootstrap.returncode, 0, bootstrap.stderr)
        not_reviewed = self.tool('record')
        self.assertNotEqual(not_reviewed.returncode, 0)
        recorded = self.tool('record', '--reviewed')
        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        cfg = json.loads(cfg_path.read_text())
        self.assertEqual(cfg['last_synced_commit'], self.target)


if __name__ == '__main__':
    unittest.main()
