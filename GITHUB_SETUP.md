# Publishing This Project to GitHub

Follow these steps to push this project to a new repository on your own
GitHub account (github.com/<your-username>).

## 1. Create the repo on GitHub

Option A -- via the web UI:
1. Go to https://github.com/new
2. Repository name: `mds-simulator` (or your preferred name)
3. Set visibility (Public/Private) as you prefer
4. Do NOT initialize with a README, .gitignore, or license (we already have them)
5. Click "Create repository"

Option B -- via GitHub CLI (if installed and authenticated with `gh auth login`):
```bash
gh repo create mds-simulator --public --source=. --remote=origin
```
(If you use Option B, you can skip step 3 below -- it creates and links the
remote for you.)

## 2. Initialize git locally and push

From inside the extracted `mds-simulator/` folder:

```bash
cd mds-simulator
git init
git add .
git commit -m "Initial commit: Cisco MDS CLI/NX-API educational simulator"
git branch -M main
```

## 3. Link to your GitHub repo and push

Replace `<your-username>` with your GitHub username:

```bash
git remote add origin https://github.com/<your-username>/mds-simulator.git
git push -u origin main
```

If you use SSH instead of HTTPS for GitHub auth:
```bash
git remote add origin git@github.com:<your-username>/mds-simulator.git
git push -u origin main
```

## 4. Verify CI runs

After pushing, go to the "Actions" tab on your GitHub repo page. The
`.github/workflows/test.yml` workflow will automatically run the test
suite (`tests/test_simulator.py`) on Python 3.10/3.11/3.12 and build the
Docker image on every push and pull request to `main`.

## 5. Optional: add repo badges to README

Once you know your repo path, you can add this to the top of README.md:

```markdown
![Tests](https://github.com/<your-username>/mds-simulator/actions/workflows/test.yml/badge.svg)
```

## Notes

- `configs/*.json` and `test_configs/` are gitignored since they contain
  runtime-generated switch state, not source code.
- The MIT LICENSE file assumes you (Kostas Labrouss) as copyright holder --
  edit if you'd like different terms or attribution.
