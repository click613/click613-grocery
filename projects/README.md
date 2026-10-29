# projects/

Each folder is one part of the pipeline (see the main README for what runs when). The README inside each folder is the original
build history, written while this ran on the old hosting: addresses like `<name>.sites.tab.bot` and steps with `publish_slow.mjs`
or a "publish" CLI describe that setup. In this repo the project scripts only write files; `pipeline/assemble_site.py` collects them
into `./site` and the GitHub workflow deploys it. Paths: every script finds the other projects through `C613_WORK` (defaults to this folder).
