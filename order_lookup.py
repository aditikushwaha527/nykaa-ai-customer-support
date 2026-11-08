
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
# 2. LOAD ORDERS
# ==========================================

def load_orders():

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
# 3. ESCALATION SCORE
# ==========================================

def calculate_escalation_score(order):

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
# 4. ESCALATION THRESHOLD
# ==========================================

def calculate_escalation_threshold():

    scores = sorted(
        calculate_escalation_score(order)
        for order in ORDERS.values()
    )

    position = 0.80 * (len(scores) - 1)

    lower_index = int(position)
    upper_index = min(lower_index + 1, len(scores) - 1)

    fraction = position - lower_index

    threshold = (
        scores[lower_index] * (1 - fraction)
        + scores[upper_index] * fraction
    )

    return round(threshold, 3)


ESCALATION_THRESHOLD = calculate_escalation_threshold()


# ==========================================
# 5. ESCALATION REASON
# ==========================================

def generate_escalation_reason(order):

    reasons = []

    if order["delayed_shipment"]:
        reasons.append("Shipment delayed")

    if order["days_since_created"] >= 30:
        reasons.append("Order age is 30 days or more")

    if not reasons:
        reasons.append(
            "Order risk score meets escalation threshold"
        )

    return "; ".join(reasons)


# ==========================================
# 6. CREATE ESCALATION TICKET
# ==========================================

def create_escalation_ticket(order, score):

    ESCALATION_QUEUE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    ticket_id = f"ESC-{order['record_id']}"

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

    existing_tickets = get_escalation_queue()

    for ticket in existing_tickets:

        if ticket["record_id"] == order["record_id"]:

            return {
                "ticket_id": ticket_id,
                "created": False,
                "message": "An escalation ticket already exists."
            }

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

    file_exists = (
        ESCALATION_QUEUE_PATH.exists()
        and ESCALATION_QUEUE_PATH.stat().st_size > 0
    )

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

        if not file_exists:
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

def check_order_status(record_id: str):

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
# 8. GET ESCALATION QUEUE
# ==========================================

def get_escalation_queue():

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
# 9. UPDATE TICKET REVIEW STATUS
# ==========================================

def update_escalation_status(ticket_id, new_status):

    allowed_statuses = [
        "Pending",
        "Under Review",
        "Resolved"
    ]

    if new_status not in allowed_statuses:
        raise ValueError("Invalid review status.")

    tickets = get_escalation_queue()

    found = False

    for ticket in tickets:

        if ticket["ticket_id"] == ticket_id:

            ticket["review_status"] = new_status
            found = True
            break

    if not found:
        return False

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

    with open(
        ESCALATION_QUEUE_PATH,
        mode="w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(tickets)

    return True
