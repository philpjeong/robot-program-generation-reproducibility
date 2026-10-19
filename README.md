# Reproducibility materials for anonymous review

This review copy supplies the complete, unchanged reproducibility archive in
small binary parts. Splitting is solely for the anonymous hosting service's
per-file size limit. Restoring the parts reproduces the original ZIP byte for
byte; it does not modify experimental responses or analysis records.

## Download and restore

1. Use **Download ZIP** on the anonymous repository page, then extract that
   download. Locate this README, `restore.py`, `manifest.json`, and all eleven
   `reproducibility.partNN.bin` files in the extracted folder. Depending on the
   download layout, they may be inside a subfolder.
2. Open a terminal in that folder and run:

   ```text
   python restore.py
   ```

   The script checks every part against `manifest.json`, joins them into
   `Supplementary_Reproducibility_Anonymous.zip`, checks the complete archive's
   SHA-256 digest, and checks each ZIP member's CRC. It uses only the Python
   standard library and makes no network requests.
3. Extract the restored ZIP. Open a terminal in its
   `supplementary_reproducibility` directory, which contains `reproduce.py`,
   `requirements.txt`, and the original package `README.md`.
4. Install the numerical dependency, if needed:

   ```text
   python -m pip install -r requirements.txt
   ```

5. Verify the saved numerical results:

   ```text
   python reproduce.py
   ```

   To include the task-characteristic correlations:

   ```text
   python reproduce.py --correlations
   ```

The numerical verification reads saved responses and analysis inputs; it does
not call models, generate new candidates, run the simulator, or execute generated
robot programs. Installing dependencies may contact a package index. Verification
outputs are written into the extracted directory, leaving the supplied ZIP
unchanged. Historical scripts that can call external services are included for
inspection but are not needed for these offline checks.

## Contents and integrity

The restored archive contains 171 files, including `saved_records.zip`, which
contains 26,904 saved files. It preserves the evidence for 7,600 condition
outcomes: 6,400 in the four-model comparison, 400 additional no-contract outcomes,
and 800 in the eight-task evaluation. Shared initial-generation outcomes are
counted once. The nested saved-record archive may remain compressed during
numerical verification. Consult the original package README for its full
inventory, provenance, implementation boundaries, and notices.

The original archive size is **76,957,617 bytes**. Its SHA-256 is:

```text
786758bf2b361e821f0a58bfca65a8669dccc3dfde5cede689b6e5594643fbff
```

This delivery wrapper grants no new blanket license. Existing notices and
third-party terms within the restored archive remain in effect. The archive's
historical availability wording describes the original package; these
instructions describe access to its unchanged anonymous review copy.
