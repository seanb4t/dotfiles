# Changelog

## [1.2.0](https://github.com/fzymgc-house/fzymgc-house-skills/compare/terraform-v1.1.0...terraform-v1.2.0) (2026-03-16)


### Features

* **superpowers:** fork obra/superpowers with jj VCS support ([#34](https://github.com/fzymgc-house/fzymgc-house-skills/issues/34)) ([1acccca](https://github.com/fzymgc-house/fzymgc-house-skills/commit/1acccca02d75627a8f7f68e0649d0406789b2b9b))

## [1.1.0](https://github.com/fzymgc-house/fzymgc-house-skills/compare/terraform-v1.0.0...terraform-v1.1.0) (2026-03-15)

### Features

* **jj:** add Jujutsu VCS support ([#31](https://github.com/fzymgc-house/fzymgc-house-skills/issues/31)) ([0ed70d0](https://github.com/fzymgc-house/fzymgc-house-skills/commit/0ed70d0223f028875f643a33d81b544cd453f33d))

## [1.0.0](https://github.com/fzymgc-house/fzymgc-house-skills/compare/terraform-v0.2.0...terraform-v1.0.0) (2026-02-28)

### ⚠ BREAKING CHANGES

* restructure into two-plugin marketplace with true agents ([#18](https://github.com/fzymgc-house/fzymgc-house-skills/issues/18))

### Features

* restructure into two-plugin marketplace with true agents ([#18](https://github.com/fzymgc-house/fzymgc-house-skills/issues/18)) ([979ea3f](https://github.com/fzymgc-house/fzymgc-house-skills/commit/979ea3fbd0c47191e32b219d8ab4152187a4e81c))

## [0.2.0](https://github.com/fzymgc-house/fzymgc-house-skills/compare/terraform-v0.1.0...terraform-v0.2.0) (2026-02-16)

### Features

* **ci:** integrate release-please for automated versioning ([#11](https://github.com/fzymgc-house/fzymgc-house-skills/issues/11)) ([8ab39f0](https://github.com/fzymgc-house/fzymgc-house-skills/commit/8ab39f0902ef55b001b4de8e94e136e442981b6c))
* **terraform:** add direct HCP API fallback for list_runs MCP bug ([4c1fdfe](https://github.com/fzymgc-house/fzymgc-house-skills/commit/4c1fdfeb85b1a2d7adf9c8e4d7b0a54dfa268ec2))
* **terraform:** add direct HCP Terraform API client ([8034c33](https://github.com/fzymgc-house/fzymgc-house-skills/commit/8034c33d1013769f91ae4d08891f6ad980661e34))
* **terraform:** add list-providers workflow ([66f01e3](https://github.com/fzymgc-house/fzymgc-house-skills/commit/66f01e311c09c96bf8b49b6391682daa3b5c3e49))
* **terraform:** add list-runs workflow ([6a2fd7e](https://github.com/fzymgc-house/fzymgc-house-skills/commit/6a2fd7e542d75128911343825e09651d1af3b5e6))
* **terraform:** add provider-docs workflow for provider documentation lookup ([b897933](https://github.com/fzymgc-house/fzymgc-house-skills/commit/b8979333f9b54d2b5cce12c3bf32cf2399ea3f84))
* **terraform:** add run-details command with formatted log output ([53677fc](https://github.com/fzymgc-house/fzymgc-house-skills/commit/53677fc1004c403ed2de04acab639501ae869c48))
* **terraform:** add run-outputs workflow to view terraform outputs ([fd33f2c](https://github.com/fzymgc-house/fzymgc-house-skills/commit/fd33f2c520bdfdab7a31660df4f634e8068b00dc))
* **terraform:** add watch-run workflow ([4196d7e](https://github.com/fzymgc-house/fzymgc-house-skills/commit/4196d7e1172dac2d34e038259f86120a5eded492))
* **terraform:** add workspace-status workflow ([cca18e2](https://github.com/fzymgc-house/fzymgc-house-skills/commit/cca18e2f81876010d0d7ee57b1bc0ac4ef5b44df))
* **terraform:** implement MCP stdio client and session manager ([5630397](https://github.com/fzymgc-house/fzymgc-house-skills/commit/5630397a7c8eb01caf46bee7dc44b497f495fe29))
* **terraform:** scaffold terraform skill directory structure ([3ff19c3](https://github.com/fzymgc-house/fzymgc-house-skills/commit/3ff19c3a7f12d2a366eda0c7c1007a90112a7921))

### Bug Fixes

* **terraform:** add SOCKS proxy support and tool permissions ([4be3317](https://github.com/fzymgc-house/fzymgc-house-skills/commit/4be3317d63a5e5afbc385e6fcb0e35cfe68d8d62))
* **terraform:** add timeout protection and improve watch-run error handling ([6d2d55b](https://github.com/fzymgc-house/fzymgc-house-skills/commit/6d2d55b1038c7631bf1d3ca304684a69651cad74))
* **terraform:** add type validation in workspace list mode ([512bbe2](https://github.com/fzymgc-house/fzymgc-house-skills/commit/512bbe2eb81063ba60bf4df47bcdccbbb4a7473f))
* **terraform:** address all PR review issues ([ddd13d1](https://github.com/fzymgc-house/fzymgc-house-skills/commit/ddd13d148ed498c6b3725341fbf9d97177eb89d4))
* **terraform:** differentiate compact format, remove unused brief flag ([0d54fef](https://github.com/fzymgc-house/fzymgc-house-skills/commit/0d54fef1eb1ad804403ac3d016f1a9fa61085cb7))
* **terraform:** improve list-runs argument validation and message truncation ([cf5236e](https://github.com/fzymgc-house/fzymgc-house-skills/commit/cf5236eba2a75adeab6ed852ae9cc4c8bf0d25c7))
* **terraform:** improve provider-docs validation and error messages ([860bc6d](https://github.com/fzymgc-house/fzymgc-house-skills/commit/860bc6d52c2f3a81c2999ae2bd7200a63d12c801))
* **terraform:** improve workspace-status data handling and validation ([eddd2ec](https://github.com/fzymgc-house/fzymgc-house-skills/commit/eddd2ecd22c4d34ab2e4e192b183a0410330edc3))
* **terraform:** prevent credential leak on temp file write failure ([7d51a35](https://github.com/fzymgc-house/fzymgc-house-skills/commit/7d51a35ba94cbf574d650abb56f23eeb6fb9add9))
* **terraform:** secure token handling, remove unused code ([a225638](https://github.com/fzymgc-house/fzymgc-house-skills/commit/a225638001b5bbf0fd0ae7b2ce310eb11ec50a3b))
* **terraform:** show apply logs for errored runs ([d641e20](https://github.com/fzymgc-house/fzymgc-house-skills/commit/d641e20f2a7185e940c09d578fa8d55811d38ea4))
* **terraform:** standardize HCP client error handling, remove redundant imports ([98d711e](https://github.com/fzymgc-house/fzymgc-house-skills/commit/98d711e56a049cdd24dac95a5e65296432bb5e8a))
