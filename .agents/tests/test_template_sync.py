from __future__ import annotations

import hashlib
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
            'last_synced_at': '2026-08-09T00:00:00+00:00' if baseline is not None else None,
            'always_manual': [],
            'ignored_paths': [],
        },
        indent=2,
    ) + '\n'


def skill() -> str:
    return '# Skill\n\n## Trigger\nX\n\n## Minimum context\nX\n\n## Procedure\nX\n\n## Safety boundary\nX\n'


def reviewed_adoption(target: str) -> dict[str, object]:
    return {
        'status': 'reviewed',
        'target_commit': target,
        'reviewed_at': '2026-08-09T00:00:00+00:00',
        'verification_repository_fingerprint': 'a' * 64,
        'prior_sync_history': [],
    }


def rewrite_plan_digest(plan: dict[str, object]) -> None:
    bound = dict(plan)
    bound.pop('created_at', None)
    bound.pop('plan_digest', None)
    bound.pop('target_ref', None)
    payload = json.dumps(bound, ensure_ascii=True, separators=(',', ':'), sort_keys=True).encode()
    plan['plan_digest'] = hashlib.sha256(payload).hexdigest()


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
        for relative in (
            '.agents/template-inheritance.json',
            '.agents/tools/_template_inheritance.py',
            '.agents/tools/_paper_profile.py',
        ):
            source = ROOT / relative
            target = self.upstream / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        shutil.copy2(ROOT / '.agents/tools/paper-init.py', self.upstream / '.agents/tools/paper-init.py')
        write(self.upstream, '.agents/tools/base.txt', 'base-v1\n')
        write(self.upstream, '.agents/tools/deleted.txt', 'delete-v1\n')
        write(self.upstream, '.agents/tools/conflict.txt', 'conflict-v1\n')
        write(self.upstream, '.agents/tools/mode-only.sh', '#!/bin/sh\nexit 0\n')
        write(self.upstream, 'future/protected.txt', 'future-v1\n')
        write(self.upstream, 'PAPER.md', 'paper-v1\n')
        write(self.upstream, 'CONTRIBUTING.md', 'contributing-v1\n')
        write(self.upstream, 'PUBLICATION.md', 'publication-v1\n')
        write(self.upstream, '.agents/tools/verify.sh', '#!/usr/bin/env bash\nexit 0\n')
        write(self.upstream, 'Makefile', "pdf:\n\t@printf '%s' '%PDF fixture' > manuscript.pdf\n")
        write(self.upstream, '.gitignore', 'manuscript.pdf\n')
        write(
            self.upstream,
            'manuscript.tex',
            '\\documentclass{article}\n\\begin{document}Fixture\\end{document}\n',
        )
        write(self.upstream, 'paper/variants/common.tex', 'variant-v1\n')
        write(
            self.upstream,
            '.agents/paper-build.json',
            json.dumps(
                {
                    'schema_version': 'paper-build-profile-v1',
                    'layout': 'external-latex',
                    'source_root': '.',
                    'entrypoint': 'manuscript.tex',
                    'bibliography': None,
                    'builds': [
                        {
                            'name': 'journal',
                            'command': ['make', 'pdf'],
                            'output': 'manuscript.pdf',
                        }
                    ],
                }
            )
            + '\n',
        )
        write(self.upstream, 'paper/custom-authored.tex', 'custom-v1\n')
        self.baseline = commit_all(self.upstream, 'template v1')

        init_repo(self.downstream)
        shutil.copytree(self.upstream / '.agents', self.downstream / '.agents')
        shutil.copy2(self.upstream / 'PAPER.md', self.downstream / 'PAPER.md')
        shutil.copy2(self.upstream / 'CONTRIBUTING.md', self.downstream / 'CONTRIBUTING.md')
        shutil.copy2(self.upstream / 'PUBLICATION.md', self.downstream / 'PUBLICATION.md')
        shutil.copy2(self.upstream / 'Makefile', self.downstream / 'Makefile')
        shutil.copy2(self.upstream / '.gitignore', self.downstream / '.gitignore')
        shutil.copy2(self.upstream / 'manuscript.tex', self.downstream / 'manuscript.tex')
        write(self.downstream, '.agents/template-sync.json', config(self.upstream, self.baseline))
        write(self.downstream, '.agents/skills/template-sync/SKILL.md', skill())
        commit_all(self.downstream, 'paper from template v1')
        git(self.downstream, 'remote', 'add', 'origin', 'git@github.com:a-green-hand-jack/example-paper.git')
        initial_head = git(self.downstream, 'rev-parse', 'HEAD').stdout.strip()
        write(
            self.downstream,
            '.agents/template-origin.json',
            json.dumps(
                {
                    'downstream_repository': 'a-green-hand-jack/example-paper',
                    'git_head': initial_head,
                    'schema_version': 'paper-template-origin-v1',
                    'template_repository': 'a-green-hand-jack/ccfa-writing-paper-template',
                    'verification': 'github_api_template_repository',
                    'verified_at': '2026-08-09T00:00:00+00:00',
                }
            ) + '\n',
        )
        write(
            self.downstream,
            '.agents/init-state.json',
            json.dumps(
                {
                    'schema_version': 'paper-init-v1',
                    'initialized_at': '2026-08-09T00:00:00+00:00',
                    'mode': 'downstream',
                    'template_cleanup': True,
                    'git_head': initial_head,
                }
            ) + '\n',
        )
        commit_all(self.downstream, 'record template lifecycle')
        git(self.downstream, 'switch', '-c', 'chore/template-sync')
        git(self.downstream, 'remote', 'add', 'template', str(self.upstream))
        git(self.downstream, 'fetch', 'template', 'main')

        write(self.upstream, '.agents/tools/base.txt', 'base-v2\n')
        write(self.upstream, '.agents/tools/conflict.txt', 'conflict-upstream-v2\n')
        write(self.upstream, '.agents/tools/new.txt', 'new-v2\n')
        (self.upstream / '.agents/tools/mode-only.sh').chmod(0o755)
        write(self.upstream, 'future/protected.txt', 'future-v2\n')
        (self.upstream / '.agents/tools/deleted.txt').unlink()
        write(self.upstream, 'PAPER.md', 'paper-upstream-v2\n')
        write(self.upstream, 'CONTRIBUTING.md', 'contributing-upstream-v2\n')
        write(self.upstream, 'PUBLICATION.md', 'publication-upstream-v2\n')
        write(self.upstream, 'Makefile', 'pdf:\n\t@true\n# template v2\n')
        write(self.upstream, 'paper/variants/common.tex', 'variant-v2\n')
        write(self.upstream, 'paper/custom-authored.tex', 'custom-v2\n')
        policy_path = self.upstream / '.agents/template-inheritance.json'
        policy = json.loads(policy_path.read_text(encoding='utf-8'))
        policy['sync']['manual_paths'].append('future/')
        policy_path.write_text(json.dumps(policy, indent=2) + '\n', encoding='utf-8')
        write(self.upstream, '.agents/tools/check-reference-integrity.py', 'sidecar checker\n')
        write(self.upstream, '.agents/dependencies/reference-integrity/uv.lock', 'locked dependency\n')
        write(self.upstream, '.agents/vendor/ccfa-skills/ccf-common/SKILL.md', '# common v2\n')
        write(self.upstream, '.agents/vendor/README.md', '# Vendored skills v2\n')
        write(self.upstream, '.agents/dependencies/vendored-skills/provenance.json', '{"schema_version":"paper-vendored-skills-v1"}\n')
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

    def remove_lifecycle_markers(self) -> None:
        for relative in ('.agents/template-origin.json', '.agents/init-state.json'):
            path = self.downstream / relative
            if path.is_symlink() or path.exists():
                path.unlink()

    def apply_and_verify(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        self.assertEqual(self.tool('apply').returncode, 0)
        verified = self.tool('verify', '--reviewed')
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)

    def test_verification_uses_declared_build_profile(self) -> None:
        self.apply_and_verify()
        report = json.loads(
            (self.downstream / '.agents/runtime/template-sync/verification.json').read_text()
        )
        self.assertEqual(
            [check['command'] for check in report['checks']],
            ['bash .agents/tools/verify.sh', 'make pdf'],
        )

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
        self.assertEqual(by_path['paper/variants/common.tex']['category'], 'manual')
        self.assertEqual(by_path['paper/custom-authored.tex']['category'], 'manual')
        self.assertEqual(by_path['future/protected.txt']['category'], 'manual')
        self.assertEqual(by_path['.agents/template-inheritance.json']['category'], 'manual')
        self.assertEqual(by_path['.agents/tools/mode-only.sh']['category'], 'safe')
        self.assertEqual(by_path['.agents/tools/mode-only.sh']['baseline_mode'], '100644')
        self.assertEqual(by_path['.agents/tools/mode-only.sh']['target_mode'], '100755')
        self.assertEqual(by_path['.agents/tools/check-reference-integrity.py']['category'], 'safe')
        self.assertEqual(by_path['.agents/dependencies/reference-integrity/uv.lock']['category'], 'manual')
        self.assertEqual(by_path['.agents/vendor/README.md']['category'], 'safe')
        self.assertEqual(by_path['.agents/vendor/ccfa-skills/ccf-common/SKILL.md']['category'], 'safe')
        self.assertEqual(by_path['.agents/dependencies/vendored-skills/provenance.json']['category'], 'safe')
        self.assertEqual(by_path['.github/workflows/reference-validation.yml']['category'], 'manual')
        self.assertEqual(by_path['REFERENCES.md']['category'], 'manual')
        self.assertEqual(by_path['references/ledger.json']['category'], 'manual')

    def test_downstream_vendor_modification_is_conflict(self) -> None:
        write(self.downstream, '.agents/vendor/ccfa-skills/ccf-common/SKILL.md', '# common downstream\n')
        commit_all(self.downstream, 'downstream vendor edit')
        plan = self.tool('plan')
        self.assertEqual(plan.returncode, 0, plan.stderr)
        data = json.loads((self.downstream / '.agents/runtime/template-sync/plan.json').read_text())
        by_path = {item['path']: item for item in data['items']}
        self.assertEqual(
            by_path['.agents/vendor/ccfa-skills/ccf-common/SKILL.md']['category'],
            'conflict',
        )

    def test_downstream_ignore_cannot_override_paper_protection(self) -> None:
        config_path = self.downstream / '.agents/template-sync.json'
        data = json.loads(config_path.read_text(encoding='utf-8'))
        data['ignored_paths'] = ['paper/']
        config_path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
        commit_all(self.downstream, 'attempt to ignore paper')

        plan = self.tool('plan')

        self.assertEqual(plan.returncode, 0, plan.stderr)
        data = json.loads((self.downstream / '.agents/runtime/template-sync/plan.json').read_text())
        by_path = {item['path']: item for item in data['items']}
        self.assertEqual(by_path['paper/custom-authored.tex']['category'], 'manual')

    def test_apply_safe_and_export_review_bundle(self) -> None:
        plan = self.tool('plan')
        self.assertEqual(plan.returncode, 0, plan.stderr)
        applied = self.tool('apply')
        self.assertEqual(applied.returncode, 0, applied.stderr)
        self.assertEqual((self.downstream / '.agents/tools/base.txt').read_text(), 'base-v2\n')
        self.assertEqual((self.downstream / '.agents/tools/new.txt').read_text(), 'new-v2\n')
        self.assertEqual((self.downstream / '.agents/tools/conflict.txt').read_text(), 'conflict-downstream\n')
        self.assertTrue((self.downstream / '.agents/tools/mode-only.sh').stat().st_mode & 0o111)
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

    def test_plan_refuses_non_regular_upstream_entry(self) -> None:
        link = self.upstream / '.agents/tools/unsafe-link'
        link.symlink_to('/tmp/template-sync-external-target')
        commit_all(self.upstream, 'template symlink')
        git(self.downstream, 'fetch', 'template', 'main')

        refused = self.tool('plan')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('refuses non-regular upstream entry', refused.stderr)
        self.assertFalse((self.downstream / '.agents/tools/unsafe-link').exists())

    def test_plan_refuses_symlinked_runtime_directory_without_touching_external_victim(self) -> None:
        runtime = self.downstream / '.agents/runtime/template-sync'
        runtime.parent.mkdir(parents=True, exist_ok=True)
        victim = Path(self.tmp.name) / 'runtime-victim'
        victim.mkdir()
        sentinel = victim / 'sentinel.txt'
        sentinel.write_text('unchanged\n')
        runtime.symlink_to(victim, target_is_directory=True)

        refused = self.tool('plan')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('symlinked template sync directory', refused.stderr)
        self.assertEqual(sentinel.read_text(), 'unchanged\n')
        self.assertFalse((victim / 'plan.json').exists())

    def test_plan_refuses_non_directory_runtime_component(self) -> None:
        runtime = self.downstream / '.agents/runtime/template-sync'
        runtime.parent.mkdir(parents=True, exist_ok=True)
        runtime.write_text('not a directory\n')

        refused = self.tool('plan')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('not a directory', refused.stderr)

    def test_plan_outputs_refuse_symlinks_without_touching_external_victim(self) -> None:
        runtime = self.downstream / '.agents/runtime/template-sync'
        runtime.mkdir(parents=True)
        victim = Path(self.tmp.name) / 'plan-victim.txt'
        victim.write_text('unchanged\n')

        for name in ('plan.json', 'plan.md'):
            with self.subTest(name=name):
                path = runtime / name
                path.unlink(missing_ok=True)
                path.symlink_to(victim)
                refused = self.tool('plan')
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('symlinked template sync', refused.stderr)
                self.assertEqual(victim.read_text(), 'unchanged\n')
                path.unlink()

    def test_apply_outputs_refuse_symlinks_without_touching_external_victim(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        runtime = self.downstream / '.agents/runtime/template-sync'
        file_victim = Path(self.tmp.name) / 'application-victim.txt'
        file_victim.write_text('unchanged\n')
        application = runtime / 'application.json'
        application.symlink_to(file_victim)

        refused_application = self.tool('apply')

        self.assertNotEqual(refused_application.returncode, 0)
        self.assertIn('symlinked template sync', refused_application.stderr)
        self.assertEqual(file_victim.read_text(), 'unchanged\n')
        self.assertEqual((self.downstream / '.agents/tools/base.txt').read_text(), 'base-v1\n')
        application.unlink()

        directory_victim = Path(self.tmp.name) / 'bundle-victim'
        directory_victim.mkdir()
        sentinel = directory_victim / 'sentinel.txt'
        sentinel.write_text('unchanged\n')
        bundle = runtime / 'merge-bundle'
        bundle.symlink_to(directory_victim, target_is_directory=True)

        refused_bundle = self.tool('apply')

        self.assertNotEqual(refused_bundle.returncode, 0)
        self.assertIn('symlinked template sync merge bundle', refused_bundle.stderr)
        self.assertEqual(sentinel.read_text(), 'unchanged\n')
        self.assertEqual((self.downstream / '.agents/tools/base.txt').read_text(), 'base-v1\n')

    def test_verification_outputs_refuse_symlinks_without_touching_external_victim(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        self.assertEqual(self.tool('apply').returncode, 0)
        runtime = self.downstream / '.agents/runtime/template-sync'
        victim = Path(self.tmp.name) / 'verification-victim.txt'
        victim.write_text('unchanged\n')

        for name in ('verification.json', 'verification.md'):
            with self.subTest(name=name):
                path = runtime / name
                path.unlink(missing_ok=True)
                path.symlink_to(victim)
                refused = self.tool('verify', '--reviewed')
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('symlinked template sync', refused.stderr)
                self.assertEqual(victim.read_text(), 'unchanged\n')
                path.unlink()

    def test_runtime_output_classes_refuse_non_regular_entries(self) -> None:
        runtime = self.downstream / '.agents/runtime/template-sync'
        runtime.mkdir(parents=True)
        for name in ('plan.json', 'plan.md'):
            with self.subTest(name=name):
                path = runtime / name
                path.mkdir()
                refused = self.tool('plan')
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('not a regular file', refused.stderr)
                path.rmdir()

        self.assertEqual(self.tool('plan').returncode, 0)
        application = runtime / 'application.json'
        application.mkdir()
        refused_application = self.tool('apply')
        self.assertNotEqual(refused_application.returncode, 0)
        self.assertIn('not a regular file', refused_application.stderr)
        application.rmdir()

        bundle = runtime / 'merge-bundle'
        bundle.write_text('not a directory\n')
        refused_bundle = self.tool('apply')
        self.assertNotEqual(refused_bundle.returncode, 0)
        self.assertIn('not a directory', refused_bundle.stderr)
        bundle.unlink()

        self.assertEqual(self.tool('apply').returncode, 0)
        for name in ('verification.json', 'verification.md'):
            with self.subTest(name=name):
                path = runtime / name
                path.mkdir()
                refused = self.tool('verify', '--reviewed')
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('not a regular file', refused.stderr)
                path.rmdir()

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

    def test_sync_commands_refuse_in_progress_adoption(self) -> None:
        path = self.downstream / '.agents/template-sync.json'
        cfg = json.loads(path.read_text())
        cfg['adoption'] = {
            'status': 'in_progress',
            'target_commit': self.target,
            'prior_sync_history': [],
        }
        cfg['last_synced_commit'] = None
        cfg['last_synced_at'] = None
        self.remove_lifecycle_markers()
        path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')

        for command in ('plan', 'apply', 'verify', 'record'):
            with self.subTest(command=command):
                result = self.tool(command, '--reviewed') if command in {'verify', 'record'} else self.tool(command)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('adoption is in_progress', result.stderr)

    def test_incomplete_in_progress_adoption_is_rejected(self) -> None:
        path = self.downstream / '.agents/template-sync.json'
        original = json.loads(path.read_text())
        invalid = (
            {'status': 'in_progress'},
            {
                'status': 'in_progress',
                'target_commit': self.target,
                'prior_sync_history': [],
                'reviewed_at': '2026-08-09T00:00:00+00:00',
            },
        )
        for adoption in invalid:
            with self.subTest(adoption=adoption):
                cfg = dict(original)
                cfg['adoption'] = adoption
                self.remove_lifecycle_markers()
                path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')
                refused = self.tool('validate')
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('in-progress adoption', refused.stderr)

    def test_local_metadata_rejects_note_and_blank_upstream(self) -> None:
        path = self.downstream / '.agents/template-sync.json'
        original = json.loads(path.read_text())
        invalid = (
            {'last_sync_note': 123},
            {'upstream': {**original['upstream'], 'remote': ' '}},
        )
        for fields in invalid:
            with self.subTest(fields=fields):
                cfg = {**original, **fields}
                path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')
                refused = self.tool('validate')
                self.assertNotEqual(refused.returncode, 0)

    def test_read_only_provenance_checks_do_not_add_missing_remote(self) -> None:
        git(self.downstream, 'remote', 'remove', 'template')
        before = git(self.downstream, 'config', '--local', '--list').stdout
        for command in ('status', 'validate'):
            with self.subTest(command=command):
                refused = self.tool(command)
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('remote template is missing', refused.stderr)
                self.assertEqual(
                    git(self.downstream, 'config', '--local', '--list').stdout,
                    before,
                )

    def test_adoption_lifecycle_rejects_template_markers(self) -> None:
        config_path = self.downstream / '.agents/template-sync.json'
        cfg = json.loads(config_path.read_text())
        cfg['adoption'] = reviewed_adoption(self.baseline)
        config_path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')
        for marker in ('.agents/template-origin.json', '.agents/init-state.json'):
            (self.downstream / marker).unlink()
        for relative, dangling in (
            ('.agents/template-origin.json', False),
            ('.agents/init-state.json', True),
        ):
            with self.subTest(relative=relative, dangling=dangling):
                path = self.downstream / relative
                if dangling:
                    path.symlink_to('missing-marker.json')
                else:
                    path.write_text('{}\n')
                refused = self.tool('validate')
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('template adoption must not carry', refused.stderr)
                path.unlink()

    def test_incomplete_reviewed_adoption_is_rejected(self) -> None:
        path = self.downstream / '.agents/template-sync.json'
        original = json.loads(path.read_text())
        invalid = (
            {'status': 'reviewed'},
            {**reviewed_adoption(self.baseline), 'reviewed_at': 'not-a-timestamp'},
            {**reviewed_adoption(self.baseline), 'verification_repository_fingerprint': 'A' * 64},
            {key: value for key, value in reviewed_adoption(self.baseline).items() if key != 'prior_sync_history'},
            {**reviewed_adoption(self.baseline), 'prior_sync_history': [{}]},
            {
                **reviewed_adoption(self.baseline),
                'prior_sync_history': [{
                    'adoption': None,
                    'last_synced_commit': self.baseline,
                    'last_synced_at': None,
                    'last_sync_note': None,
                    'reference_integrity': None,
                    'upstream': {
                        'url': str(self.upstream),
                        'remote': 'template',
                        'branch': 'main',
                    },
                }],
            },
        )
        for adoption in invalid:
            with self.subTest(adoption=adoption):
                cfg = dict(original)
                cfg['adoption'] = adoption
                self.remove_lifecycle_markers()
                path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')
                refused = self.tool('validate')
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('reviewed adoption', refused.stderr)

    def test_reviewed_adoption_requires_valid_top_level_sync_timestamp(self) -> None:
        path = self.downstream / '.agents/template-sync.json'
        original = json.loads(path.read_text())
        for synced_at in ('not-a-timestamp', None):
            with self.subTest(synced_at=synced_at):
                cfg = dict(original)
                cfg['adoption'] = reviewed_adoption(self.baseline)
                self.remove_lifecycle_markers()
                cfg['last_synced_commit'] = self.baseline
                cfg['last_synced_at'] = synced_at
                path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')
                refused = self.tool('validate')
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('last_synced', refused.stderr)

    def test_reviewed_adoption_target_cannot_be_newer_than_current_baseline(self) -> None:
        path = self.downstream / '.agents/template-sync.json'
        cfg = json.loads(path.read_text())
        cfg['adoption'] = reviewed_adoption(self.target)
        self.remove_lifecycle_markers()
        path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')

        refused = self.tool('validate')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('equal to or an ancestor', refused.stderr)

    def test_reviewed_adoption_rejects_unrelated_recorded_baseline(self) -> None:
        path = self.downstream / '.agents/template-sync.json'
        cfg = json.loads(path.read_text())
        cfg['last_synced_commit'] = git(self.downstream, 'rev-parse', 'HEAD').stdout.strip()
        cfg['adoption'] = reviewed_adoption(self.baseline)
        self.remove_lifecycle_markers()
        path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')

        refused = self.tool('validate')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('not reachable from configured upstream', refused.stderr)

    def test_reviewed_adoption_rejects_unrelated_target_provenance(self) -> None:
        path = self.downstream / '.agents/template-sync.json'
        cfg = json.loads(path.read_text())
        unrelated = git(self.downstream, 'rev-parse', 'HEAD').stdout.strip()
        cfg['adoption'] = reviewed_adoption(unrelated)
        self.remove_lifecycle_markers()
        path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')

        refused = self.tool('validate')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('not reachable from configured upstream', refused.stderr)

    def test_operational_paths_validate_reviewed_provenance_before_action(self) -> None:
        path = self.downstream / '.agents/template-sync.json'
        cfg = json.loads(path.read_text())
        cfg['adoption'] = reviewed_adoption(git(self.downstream, 'rev-parse', 'HEAD').stdout.strip())
        self.remove_lifecycle_markers()
        path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')

        commands = (('plan',), ('apply',), ('verify', '--reviewed'), ('record', '--reviewed'))
        for command in commands:
            with self.subTest(command=command):
                refused = self.tool(*command)
                self.assertNotEqual(refused.returncode, 0)
                self.assertIn('not reachable from configured upstream', refused.stderr)

    def test_fetch_restores_missing_remote_ref_before_reviewed_provenance_validation(self) -> None:
        path = self.downstream / '.agents/template-sync.json'
        cfg = json.loads(path.read_text())
        cfg['adoption'] = reviewed_adoption(self.baseline)
        self.remove_lifecycle_markers()
        path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')
        git(self.downstream, 'update-ref', '-d', 'refs/remotes/template/main')

        blocked = self.tool('validate')
        self.assertNotEqual(blocked.returncode, 0)
        self.assertIn('fetch first', blocked.stderr)

        fetched = self.tool('fetch')
        self.assertEqual(fetched.returncode, 0, fetched.stdout + fetched.stderr)
        self.assertEqual(self.tool('validate').returncode, 0)

    def test_plan_fetch_restores_missing_remote_and_remote_ref(self) -> None:
        git(self.downstream, 'update-ref', '-d', 'refs/remotes/template/main')
        git(self.downstream, 'remote', 'remove', 'template')

        planned = self.tool('plan', '--fetch')

        self.assertEqual(planned.returncode, 0, planned.stdout + planned.stderr)
        self.assertEqual(
            git(self.downstream, 'remote', 'get-url', 'template').stdout.strip(),
            str(self.upstream),
        )
        self.assertEqual(
            git(self.downstream, 'rev-parse', 'refs/remotes/template/main').returncode,
            0,
        )

    def test_plan_rejects_remote_url_mismatch(self) -> None:
        git(self.downstream, 'remote', 'set-url', 'template', str(self.downstream))

        refused = self.tool('plan')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('expected', refused.stderr)

    def test_plan_rejects_arbitrary_local_target(self) -> None:
        refused = self.tool('plan', '--target-ref', 'HEAD')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('not reachable from configured upstream', refused.stderr)

    def test_plan_rejects_commit_from_unconfigured_upstream_ref(self) -> None:
        git(self.upstream, 'switch', '-c', 'side')
        write(self.upstream, '.agents/tools/side.txt', 'side only\n')
        commit_all(self.upstream, 'side target')
        git(self.downstream, 'fetch', 'template', 'side:refs/remotes/template/side')

        refused = self.tool('plan', '--target-ref', 'template/side')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('not reachable from configured upstream', refused.stderr)

    def test_verify_rejects_skipped_safe_modification_with_receipt(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        self.assertEqual(self.tool('apply').returncode, 0)
        write(self.downstream, '.agents/tools/base.txt', 'base-v1\n')
        git(self.downstream, 'add', '.agents/tools/base.txt')

        refused = self.tool('verify', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('not fully applied and staged', refused.stderr)

    def test_verify_rejects_skipped_safe_addition_with_receipt(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        self.assertEqual(self.tool('apply').returncode, 0)
        git(self.downstream, 'rm', '-f', '.agents/tools/new.txt')

        refused = self.tool('verify', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('not fully applied and staged', refused.stderr)

    def test_verify_rejects_skipped_safe_deletion_with_receipt(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        self.assertEqual(self.tool('apply').returncode, 0)
        git(self.downstream, 'restore', '--source', 'HEAD', '--staged', '--worktree', '.agents/tools/deleted.txt')

        refused = self.tool('verify', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('not fully applied and staged', refused.stderr)

    def test_verify_rejects_unstaged_safe_change_with_receipt(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        self.assertEqual(self.tool('apply').returncode, 0)
        git(self.downstream, 'restore', '--staged', '.agents/tools/base.txt')

        refused = self.tool('verify', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('not fully applied and staged', refused.stderr)

    def test_verify_reconstructs_policy_despite_forged_plan_and_receipt(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        runtime = self.downstream / '.agents/runtime/template-sync'
        plan_path = runtime / 'plan.json'
        plan = json.loads(plan_path.read_text())
        base = next(item for item in plan['items'] if item['path'] == '.agents/tools/base.txt')
        base['category'] = 'manual'
        plan['counts']['safe'] -= 1
        plan['counts']['manual'] += 1
        rewrite_plan_digest(plan)
        plan_path.write_text(json.dumps(plan, indent=2, sort_keys=True) + '\n')
        receipt = {
            'schema_version': 'paper-template-sync-application-v1',
            'repository_id': plan['repository_id'],
            'downstream_branch': plan['downstream_branch'],
            'downstream_head': plan['downstream_head'],
            'downstream_tree': plan['downstream_tree'],
            'baseline': plan['baseline'],
            'target_commit': plan['target_commit'],
            'plan_digest': plan['plan_digest'],
        }
        (runtime / 'application.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')

        refused = self.tool('verify', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('original policy and classification', refused.stderr)

    def test_apply_recomputes_policy_and_rejects_reclassified_protected_path(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        path = self.downstream / '.agents/runtime/template-sync/plan.json'
        plan = json.loads(path.read_text())
        paper = next(item for item in plan['items'] if item['path'] == 'PAPER.md')
        paper['category'] = 'safe'
        plan['counts']['manual'] -= 1
        plan['counts']['safe'] += 1
        rewrite_plan_digest(plan)
        path.write_text(json.dumps(plan, indent=2, sort_keys=True) + '\n')

        refused = self.tool('apply')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('policy and classification', refused.stderr)
        self.assertEqual((self.downstream / 'PAPER.md').read_text(), 'paper-v1\n')

    def test_apply_rejects_different_branch_at_same_head(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        git(self.downstream, 'switch', '-c', 'chore/template-sync-other')

        refused = self.tool('apply')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('branch changed', refused.stderr)
        self.assertEqual((self.downstream / '.agents/tools/base.txt').read_text(), 'base-v1\n')

    def test_apply_retains_moved_head_rejection(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        write(self.downstream, 'checkpoint.txt', 'new head\n')
        commit_all(self.downstream, 'move downstream head')

        refused = self.tool('apply')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('HEAD moved', refused.stderr)
        self.assertEqual((self.downstream / '.agents/tools/base.txt').read_text(), 'base-v1\n')

    def test_record_reviewed_rejects_missing_plan_and_report(self) -> None:
        refused = self.tool('record', '--reviewed')
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('plan', refused.stderr)

    def test_record_reviewed_rejects_missing_verification_report(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        self.assertEqual(self.tool('apply').returncode, 0)

        refused = self.tool('record', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('verification report', refused.stderr)

    def test_record_reviewed_rejects_default_branch(self) -> None:
        git(self.downstream, 'switch', 'main')
        refused = self.tool('record', '--reviewed')
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('default branch', refused.stderr)

    def test_record_rejects_unrelated_dirty_state_after_verification(self) -> None:
        self.apply_and_verify()
        write(self.downstream, 'unrelated.txt', 'not part of sync\n')

        refused = self.tool('record', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('unrelated dirty state', refused.stderr)

    def test_record_rejects_stale_verification_after_planned_file_changes(self) -> None:
        self.apply_and_verify()
        write(self.downstream, 'PAPER.md', 'review changed after verification\n')

        refused = self.tool('record', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('changed since template sync verification', refused.stderr)

    def test_record_rejects_stale_verification_after_index_only_change(self) -> None:
        self.apply_and_verify()
        paper = self.downstream / 'PAPER.md'
        paper.write_text('index-only mutation\n', encoding='utf-8')
        git(self.downstream, 'add', 'PAPER.md')
        paper.write_text('paper-v1\n', encoding='utf-8')

        refused = self.tool('record', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('changed since template sync verification', refused.stderr)

    def test_verify_rejects_build_command_index_mutation(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        self.assertEqual(self.tool('apply').returncode, 0)
        makefile = self.downstream / 'Makefile'
        makefile.write_text(
            'pdf:\n'
            "\tprintf 'index mutation\\n' > PAPER.md\n"
            '\tgit add PAPER.md\n'
            "\tprintf 'paper-v1\\n' > PAPER.md\n"
            "\tprintf '%s' '%PDF fixture' > manuscript.pdf\n",
            encoding='utf-8',
        )

        refused = self.tool('verify', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('changed tracked, staged, or non-runtime untracked', refused.stderr)
        report = json.loads(
            (self.downstream / '.agents/runtime/template-sync/verification.json').read_text()
        )
        self.assertFalse(report['repository_unchanged'])

    def test_verify_rejects_build_command_ignored_authored_mutation(self) -> None:
        style = self.downstream / 'results.out'
        style.write_text('original\n')
        with (self.downstream / '.gitignore').open('a') as ignore:
            ignore.write('results.out\n')
        commit_all(self.downstream, 'ignore local publisher style')
        self.assertEqual(self.tool('plan').returncode, 0)
        self.assertEqual(self.tool('apply').returncode, 0)
        makefile = self.downstream / 'Makefile'
        makefile.write_text(
            "pdf:\n\tprintf 'changed\\n' > results.out\n\tprintf '%s' '%PDF fixture' > paper/main.pdf\n"
        )
        refused = self.tool('verify', '--reviewed')
        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('changed tracked, staged, or non-runtime untracked', refused.stderr)

    def test_verify_ignores_python_cache_created_by_build(self) -> None:
        makefile = self.downstream / 'Makefile'
        makefile.write_text(
            "pdf:\n\tmkdir -p .gitignored/__pycache__\n"
            "\tprintf 'cache' > .gitignored/__pycache__/module.cpython-312.pyc\n"
            "\tprintf '%s' '%PDF fixture' > manuscript.pdf\n"
        )
        with (self.downstream / '.gitignore').open('a') as ignore:
            ignore.write('.gitignored/\n')
        commit_all(self.downstream, 'declare cache-producing build')
        self.assertEqual(self.tool('plan').returncode, 0)
        self.assertEqual(self.tool('apply').returncode, 0)
        refused = self.tool('verify', '--reviewed')
        self.assertEqual(refused.returncode, 0, refused.stdout + refused.stderr)

    def test_record_rejects_tampered_verification_binding(self) -> None:
        self.apply_and_verify()
        path = self.downstream / '.agents/runtime/template-sync/verification.json'
        report = json.loads(path.read_text())
        report['target_commit'] = self.baseline
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')

        refused = self.tool('record', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('stale target_commit', refused.stderr)

    def test_record_reexecutes_commands_despite_forged_success_report(self) -> None:
        self.assertEqual(self.tool('plan').returncode, 0)
        self.assertEqual(self.tool('apply').returncode, 0)
        write(self.downstream, 'Makefile', 'pdf:\n\t@false\n')
        failed = self.tool('verify', '--reviewed')
        self.assertNotEqual(failed.returncode, 0)
        path = self.downstream / '.agents/runtime/template-sync/verification.json'
        report = json.loads(path.read_text())
        report['success'] = True
        for check in report['checks']:
            check['returncode'] = 0
            check['success'] = True
        path.write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')

        refused = self.tool('record', '--reviewed')

        self.assertNotEqual(refused.returncode, 0)
        self.assertIn('failed during record', refused.stderr)

    def test_reviewed_adoption_allows_later_baseline_advancement(self) -> None:
        path = self.downstream / '.agents/template-sync.json'
        cfg = json.loads(path.read_text())
        cfg['adoption'] = reviewed_adoption(self.baseline)
        self.remove_lifecycle_markers()
        path.write_text(json.dumps(cfg, indent=2, sort_keys=True) + '\n')
        commit_all(self.downstream, 'record reviewed adoption metadata')

        self.apply_and_verify()
        recorded = self.tool('record', '--reviewed')

        self.assertEqual(recorded.returncode, 0, recorded.stdout + recorded.stderr)
        advanced = json.loads(path.read_text())
        self.assertEqual(advanced['adoption']['status'], 'reviewed')
        self.assertEqual(advanced['last_synced_commit'], self.target)

    def test_bootstrap_and_record(self) -> None:
        cfg_path = self.downstream / '.agents/template-sync.json'
        cfg = json.loads(cfg_path.read_text())
        cfg['last_synced_commit'] = None
        cfg['last_synced_at'] = None
        cfg_path.write_text(json.dumps(cfg, indent=2) + '\n')
        commit_all(self.downstream, 'remove baseline')
        no_bootstrap = self.tool('plan')
        self.assertNotEqual(no_bootstrap.returncode, 0)
        self.assertIn('--bootstrap', no_bootstrap.stderr)
        bootstrap = self.tool('plan', '--bootstrap')
        self.assertEqual(bootstrap.returncode, 0, bootstrap.stderr)
        not_reviewed = self.tool('record')
        self.assertNotEqual(not_reviewed.returncode, 0)
        applied = self.tool('apply')
        self.assertEqual(applied.returncode, 0, applied.stderr)
        verified = self.tool('verify', '--reviewed')
        self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
        recorded = self.tool('record', '--reviewed')
        self.assertEqual(recorded.returncode, 0, recorded.stderr)
        cfg = json.loads(cfg_path.read_text())
        self.assertEqual(cfg['last_synced_commit'], self.target)


if __name__ == '__main__':
    unittest.main()
