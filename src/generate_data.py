import random
import uuid
from datetime import datetime, timezone
import json
from pathlib import Path
import argparse


def generate_transaction():
    return {
        "transaction_id": str(uuid.uuid4()),
        "customer_id": random.randint(1, 10000),
        "product_id": random.randint(1, 500),
        "quantity": random.randint(1, 10),
        "unit_price": round(random.uniform(5, 500), 2),
        "region": random.choice(
            ["Europe", "Asia", "America"]
        ),
        "timestamp": datetime.now(timezone.utc).isoformat()
    }

def generate_batch(batch_id, record_count, output_dir):
    transactions = [
        generate_transaction()
        for _ in range(record_count)
    ]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    file_path = output_dir / f"batch_{batch_id:04d}.json"

    with file_path.open("w", encoding="utf-8") as file:
        json.dump(transactions, file)

    return file_path

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("--batches", type=int, default=10)
    parser.add_argument("--records", type=int, default=1000)
    parser.add_argument("--output", default="data/raw")

    args = parser.parse_args()

    for batch_id in range(1, args.batches + 1):
        file_path = generate_batch(
            batch_id,
            args.records,
            args.output
        )

        print(f"Generated: {file_path}")


if __name__ == "__main__":
    main()



