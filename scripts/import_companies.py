"""Import AmbitionBox company CSV into MongoDB."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from controllers.company_controller import CompanyController
from configs.db.mongo_conn import init_db


def main() -> None:
    init_db()
    count = CompanyController.import_from_csv()
    print(f"Imported/updated companies from CSV: {count}")


if __name__ == "__main__":
    main()
