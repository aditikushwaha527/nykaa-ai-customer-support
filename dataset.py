
import csv
import random
from pathlib import Path

# Dataset design choices for the Nykaa capstone
SEED = 42
NUM_ORDERS = 50

CATEGORIES = [
    "Apparel",
    "Electronics",
    "Home",
    "Footwear",
    "Beauty",
]

STATUSES = [
    "Placed",
    "Shipped",
    "Delivered",
    "Returned",
    "Refunded",
]

# Realistic fictional order values in Indian rupees.
MIN_ORDER_VALUE = 199
MAX_ORDER_VALUE = 14999


def generate_orders():
    """Generate reproducible fictional Nykaa order records."""
    rng = random.Random(SEED)
    orders = []

    # Balanced category and status coverage.
    # Each category and status appears at least once,
    # and every category appears at least 3 times.
    categories = [
        CATEGORIES[i % len(CATEGORIES)]
        for i in range(NUM_ORDERS)
    ]
    statuses = [
        STATUSES[i % len(STATUSES)]
        for i in range(NUM_ORDERS)
    ]

    # Shuffle deterministically to avoid a fixed repeating order.
    rng.shuffle(categories)
    rng.shuffle(statuses)

    # Generate a reproducible 20% delayed-shipment rate.
    delayed_flags = [True] * (NUM_ORDERS // 5)
    delayed_flags += [
        False
    ] * (NUM_ORDERS - len(delayed_flags))
    rng.shuffle(delayed_flags)

    for i in range(NUM_ORDERS):
        orders.append({
            "record_id": f"NYK{i + 1:04d}",
            "category": categories[i],
            "status": statuses[i],
            "order_value_inr": rng.randint(
                MIN_ORDER_VALUE, MAX_ORDER_VALUE
            ),
            "days_since_created": rng.randint(0, 30),
            "delayed_shipment": delayed_flags[i],
        })

    return orders


def validate_orders(orders):
    """Validate all structural requirements in the assignment."""
    assert len(orders) >= 40, "Need at least 40 records."

    required_fields = {
        "record_id",
        "category",
        "status",
        "order_value_inr",
        "days_since_created",
        "delayed_shipment",
    }

    assert all(
        set(order.keys()) == required_fields
        for order in orders
    ), "Record fields do not match the required schema."

    assert len({
        order["record_id"] for order in orders
    }) == len(orders), "Duplicate record IDs found."

    category_counts = {
        category: sum(
            order["category"] == category for order in orders
        )
        for category in CATEGORIES
    }

    status_counts = {
        status: sum(
            order["status"] == status for order in orders
        )
        for status in STATUSES
    }

    assert all(
        count >= 3 for count in category_counts.values()
    ), "Every required category needs at least 3 records."

    assert all(
        count >= 1 for count in status_counts.values()
    ), "Every required status must appear at least once."

    assert all(
        MIN_ORDER_VALUE <= order["order_value_inr"] <= MAX_ORDER_VALUE
        for order in orders
    ), "Order value outside the chosen range."

    assert all(
        isinstance(order["days_since_created"], int)
        and 0 <= order["days_since_created"] <= 30
        for order in orders
    ), "days_since_created must be an integer from 0 to 30."

    assert all(
        isinstance(order["delayed_shipment"], bool)
        for order in orders
    ), "delayed_shipment must be a Boolean."

    delayed_count = sum(
        order["delayed_shipment"] for order in orders
    )
    delayed_percentage = delayed_count / len(orders) * 100

    assert 10 <= delayed_percentage <= 30, (
        "Delayed shipment percentage must be between 10% and 30%."
    )

    return category_counts, status_counts, delayed_percentage


if __name__ == "__main__":
    orders = generate_orders()

    # Check that the same seed generates the same records.
    assert orders == generate_orders(), (
        "Dataset generation is not deterministic."
    )

    category_counts, status_counts, delayed_percentage = (
        validate_orders(orders)
    )

    # Keep the dataset inside the project folder.
    output_dir = Path(__file__).parent / "data"
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "nykaa_orders.csv"

    with open(
        output_file, "w", newline="", encoding="utf-8"
    ) as file:
        writer = csv.DictWriter(
            file, fieldnames=orders[0].keys()
        )
        writer.writeheader()
        writer.writerows(orders)

    print("=" * 45)
    print("NYKAA CAPSTONE DATASET VALIDATION")
    print("=" * 45)

    print(f"\nTotal records: {len(orders)}")
    print(f"Random seed: {SEED}")

    print("\nCategory counts:")
    for category, count in category_counts.items():
        print(f"  {category}: {count}")

    print("\nStatus counts:")
    for status, count in status_counts.items():
        print(f"  {status}: {count}")

    print(
        f"\nDelayed shipments: {delayed_percentage:.1f}%"
    )
    print(
        f"Order value range: ₹{MIN_ORDER_VALUE:,}"
        f"–₹{MAX_ORDER_VALUE:,}"
    )
    print("Validation: PASSED")
    print(f"CSV saved to: {output_file}")


