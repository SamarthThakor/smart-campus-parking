# Recorded verification
Date: October 6, 2026
Runtime: Windows, Python 3.12.14, Flask 3.1.3, SQLAlchemy 2.1.3.
Database: temporary SQLite databases for tests; file-based SQLite for live HTTP demo.

- 28 pytest cases passed.
- Python syntax compilation passed.
- Local source-change watcher detected an edit and reran all 28 cases successfully.
- JavaScript syntax check passed using Node.js --check.
- Live HTTP health check returned 200.
- Student recommendation changed from Lot B to Lot A after an admin closed Lot B.
- The demo restored Lot B afterward.
- Schema definitions compiled to MySQL DDL; MySQL execution was not tested.
- GitHub Actions configuration is included; a hosted run is pending publication.
- Browser UI automation was unavailable in this environment; no browser test pass is claimed.

Raw evidence: local-checks.txt and http-demo.json.
