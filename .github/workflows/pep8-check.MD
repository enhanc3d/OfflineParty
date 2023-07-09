name: PEP8 Check

on:
  push:
    branches:
      - main

jobs:
  pep8_check:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.x
      - name: Install dependencies
        run: pip install flake8
      - name: Run PEP8 check
        run: |
          flake8 --max-line-length 120 --ignore=E501 --exit-zero . | awk -F: 'BEGIN{OFS=":"; last=""} {if($1!=last){print "["$1"](https://github.com/"ENVIRON["GITHUB_REPOSITORY"]"/blob/"ENVIRON["GITHUB_REF"]"/"$1")\n```"; last=$1} print $1,$2,$3,$4"\n```"}' > pep8_issues.txt
        env:
          GITHUB_REPOSITORY: ${{ github.repository }}
          GITHUB_REF: ${{ github.ref }}
      - name: Upload PEP8 issues
        uses: actions/upload-artifact@v2
        with:
          name: pep8_issues
          path: pep8_issues.txt

  create_issue:
    needs: pep8_check
    runs-on: ubuntu-latest
    steps:
      - name: Download PEP8 issues
        uses: actions/download-artifact@v2
        with:
          name: pep8_issues
      - name: Save issue output
        id: save_output
        run: |
          ISSUE_OUTPUT=$(cat pep8_issues.txt)
          echo "---" > issue_template.md
          echo "title: '🔥 PEP8 issues found 🔥'" >> issue_template.md
          echo "---" >> issue_template.md
          echo "The following PEP8 issues were found:" >> issue_template.md
          echo "$ISSUE_OUTPUT" >> issue_template.md
      - name: Create an issue
        uses: JasonEtco/create-an-issue@v2.9.1
        env:
          GITHUB_TOKEN: ${{ secrets.YOUR_SECRET_NAME }}
        with:
          filename: issue_template.md


