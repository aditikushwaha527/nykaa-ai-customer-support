
import csv
from pathlib import Path
from datetime import datetime


# ==========================================
# 1. PROJECT PATHS
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parent

DATASET_PATH = PROJECT_DIR / "data" / "nykaa_orders.csv"

ESCALATION_QUEUE_PATH = (
    PROJECT_DIR / "data" / "escalation_queue.csv"
)


# ==========================================
# 2. LOAD CUSTOMER ORDERS
# ==========================================

def load_orders():
    """Load fictional Nykaa orders from CSV."""

    orders = {}

    with open(
        DATASET_PATH,
        mode="r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        for row in reader:

            record_id = row["record_id"]

            orders[record_id] = {
                "record_id": record_id,
                "category": row["category"],
                "status": row["status"],
                "order_value_inr": float(row["order_value_inr"]),
                "days_since_created": int(row["days_since_created"]),
                "delayed_shipment": (
                    row["delayed_shipment"].strip().lower() == "true"
                )
            }

    return orders


ORDERS = load_orders()


# ==========================================
# 3. ESCALATION SCORE CALCULATION
# ==========================================

def calculate_escalation_score(order):
    """
    Calculate escalation score between 0 and 1.

    Delayed shipment contributes 60%.
    Order age contributes 40%.
    """

    delay_component = (
        1.0 if order["delayed_shipment"] else 0.0
    )

    age_component = order["days_since_created"] / 30

    score = (
        0.60 * delay_component
        + 0.40 * age_component
    )

    return round(score, 3)


# ==========================================
# 4. CALCULATE ESCALATION THRESHOLD
# ==========================================

def calculate_escalation_threshold():
    """Calculate the 80th percentile of order scores."""

    scores = sorted(
        calculate_escalation_score(order)
        for order in ORDERS.values()
    )

    position = 0.80 * (len(scores) - 1)

    lower_index = int(position)
    upper_index = min(
        lower_index + 1,
        len(scores) - 1
    )

    fraction = position - lower_index

    threshold = (
        scores[lower_index] * (1 - fraction)
        + scores[upper_index] * fraction
    )

    return round(threshold, 3)


ESCALATION_THRESHOLD = calculate_escalation_threshold()


# ==========================================
# 5. GENERATE ESCALATION REASON
# ==========================================

def generate_escalation_reason(order):

    reasons = []

    if order["delayed_shipment"]:
        reasons.append("Shipment delayed")

    if order["days_since_created"] >= 30:
        reasons.append("Order age is 30 days or more")

    if not reasons:
        reasons.append(
            "Order risk score meets the escalation threshold"
        )

    return "; ".join(reasons)


# ==========================================
# 6. CREATE HUMAN ESCALATION TICKET
# ==========================================

def create_escalation_ticket(order, score):
    """
    Create a pending human-review ticket.

    Prevent duplicate tickets for the same order.
    """

    ESCALATION_QUEUE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ticket_id = f"ESC-{order['record_id']}"

    # Define queue columns.
    fieldnames = [
        "ticket_id",
        "record_id",
        "category",
        "order_status",
        "order_value_inr",
        "escalation_score",
        "escalation_threshold",
        "reason",
        "review_status",
        "created_at"
    ]

    # Check whether a ticket already exists.
    existing_ticket = False

    if ESCALATION_QUEUE_PATH.exists():

        with open(
            ESCALATION_QUEUE_PATH,
            mode="r",
            newline="",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(file)

            for row in reader:

                if row.get("record_id") == order["record_id"]:
                    existing_ticket = True
                    break

    if existing_ticket:
        return {
            "ticket_id": ticket_id,
            "created": False,
            "message": "An escalation ticket already exists."
        }

    # Prepare the new ticket.
    ticket = {
        "ticket_id": ticket_id,
        "record_id": order["record_id"],
        "category": order["category"],
        "order_status": order["status"],
        "order_value_inr": order["order_value_inr"],
        "escalation_score": score,
        "escalation_threshold": ESCALATION_THRESHOLD,
        "reason": generate_escalation_reason(order),
        "review_status": "Pending",
        "created_at": datetime.now().isoformat(
            timespec="seconds"
        )
    }

    # Add the ticket to the CSV queue.
    file_exists = ESCALATION_QUEUE_PATH.exists()

    with open(
        ESCALATION_QUEUE_PATH,
        mode="a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        if not file_exists or ESCALATION_QUEUE_PATH.stat().st_size == 0:
            writer.writeheader()

        writer.writerow(ticket)

    return {
        "ticket_id": ticket_id,
        "created": True,
        "message": "Escalation ticket created successfully."
    }


# ==========================================
# 7. CHECK ORDER STATUS
# ==========================================

def check_order_status(record_id: str) -> dict:
    """Look up an order and check its escalation requirement."""

    order = ORDERS.get(record_id)

    if order is None:

        return {
            "found": False,
            "record_id": record_id,
            "message": "Order ID not found."
        }

    score = calculate_escalation_score(order)

    requires_escalation = (
        score >= ESCALATION_THRESHOLD
    )

    ticket_result = None

    if requires_escalation:

        ticket_result = create_escalation_ticket(
            order,
            score
        )

    return {
        "found": True,
        "record_id": order["record_id"],
        "category": order["category"],
        "status": order["status"],
        "order_value_inr": order["order_value_inr"],
        "days_since_created": order["days_since_created"],
        "delayed_shipment": order["delayed_shipment"],
        "escalation_score": score,
        "escalation_threshold": ESCALATION_THRESHOLD,
        "requires_escalation": requires_escalation,
        "escalation_ticket": ticket_result
    }


# ==========================================
# 8. VIEW ESCALATION QUEUE
# ==========================================

def get_escalation_queue():
    """Return all tickets awaiting or undergoing review."""

    if not ESCALATION_QUEUE_PATH.exists():
        return []

    with open(
        ESCALATION_QUEUE_PATH,
        mode="r",
        newline="",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(file)

        return list(reader)


# ==========================================
# 9. TEST THE ESCALATION SYSTEM
# ==========================================

if __name__ == "__main__":

    print("=" * 55)
    print("NYKAA ORDER AND ESCALATION SYSTEM")
    print("=" * 55)

    print("\nTOTAL ORDERS:", len(ORDERS))

    print(
        "ESCALATION THRESHOLD:",
        ESCALATION_THRESHOLD
    )

    # Find an order that meets the escalation threshold.
    flagged_orders = [
        order
        for order in ORDERS.values()
        if calculate_escalation_score(order)
        >= ESCALATION_THRESHOLD
    ]

    if flagged_orders:

        sample_order = flagged_orders[0]

        print("\nTESTING AN ESCALATION-ELIGIBLE ORDER:")

        result = check_order_status(
            sample_order["record_id"]
        )

        print(result)

    else:

        print("\nNo escalation-eligible orders found.")

    print("\nCURRENT ESCALATION QUEUE:")

    queue = get_escalation_queue()

    for ticket in queue:
        print(ticket)

    print("\nTOTAL ESCALATION TICKETS:", len(queue))

    print("\nESCALATION SYSTEM TEST COMPLETED!")
