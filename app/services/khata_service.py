from app.database.db import SessionLocal
from app.database.models import Customer, KhataTransaction


def _compute_balance(transactions):
    balance = 0
    for transaction in transactions:
        if transaction.transaction_type == "CREDIT":
            balance += transaction.amount
        elif transaction.transaction_type == "PAYMENT":
            balance -= transaction.amount
    return balance


def find_or_create_customer(name, phone=None):
    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.name.ilike(name))
            .first()
        )

        if not customer:
            customer = Customer(
                name=name,
                phone=phone
            )
            db.add(customer)
            db.commit()
            db.refresh(customer)

            message = "Customer created successfully."
        else:
            message = "Customer found."

        return {
            "success": True,
            "customer_id": customer.id,
            "name": customer.name,
            "phone": customer.phone,
            "message": message
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()


def get_customer_balance(customer_id):
    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return {
                "success": False,
                "message": "Customer not found."
            }

        transactions = (
            db.query(KhataTransaction)
            .filter(
                KhataTransaction.customer_id == customer_id
            )
            .all()
        )

        balance = 0

        for transaction in transactions:
            if transaction.transaction_type == "CREDIT":
                balance += transaction.amount
            elif transaction.transaction_type == "PAYMENT":
                balance -= transaction.amount

        return {
            "success": True,
            "customer_id": customer.id,
            "customer": customer.name,
            "balance": round(balance, 2)
        }

    finally:
        db.close()


def add_credit(customer_id, amount, reference=None):
    db = SessionLocal()

    try:
        if amount <= 0:
            return {
                "success": False,
                "message": "Credit amount must be greater than zero."
            }

        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return {
                "success": False,
                "message": "Customer not found."
            }

        transaction = KhataTransaction(
            customer_id=customer_id,
            transaction_type="CREDIT",
            amount=amount,
            reference=reference
        )

        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "message": "Credit added successfully.",
            "customer": customer.name,
            "amount": round(amount, 2)
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()


def record_payment(customer_id, amount, reference=None):
    db = SessionLocal()

    try:
        if amount <= 0:
            return {
                "success": False,
                "message": "Payment amount must be greater than zero."
            }

        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return {
                "success": False,
                "message": "Customer not found."
            }

        # Calculate current balance
        transactions = (
            db.query(KhataTransaction)
            .filter(
                KhataTransaction.customer_id == customer_id
            )
            .all()
        )

        balance = 0

        for transaction in transactions:
            if transaction.transaction_type == "CREDIT":
                balance += transaction.amount
            elif transaction.transaction_type == "PAYMENT":
                balance -= transaction.amount

        # Prevent over-settlement
        if amount > balance:
            return {
                "success": False,
                "message": (
                    f"Payment exceeds outstanding balance. "
                    f"Current balance: ₹{balance:.2f}."
                )
            }

        transaction = KhataTransaction(
            customer_id=customer_id,
            transaction_type="PAYMENT",
            amount=amount,
            reference=reference
        )

        db.add(transaction)
        db.commit()

        return {
            "success": True,
            "message": "Payment recorded successfully.",
            "customer": customer.name,
            "payment": round(amount, 2),
            "remaining_balance": round(balance - amount, 2)
        }

    except Exception as e:
        db.rollback()
        return {
            "success": False,
            "message": str(e)
        }

    finally:
        db.close()


def get_customers_with_outstanding_balance():
    """
    List every customer with a positive khata balance, for payment
    reminders. Cheapest possible version of "khata payment
    reminders": the owner asks the agent who owes money, the agent
    returns the list; wiring it to an actual SMS/WhatsApp send is a
    connector-level concern outside this project's scope.
    """

    db = SessionLocal()

    try:
        customers = db.query(Customer).all()
        results = []

        for customer in customers:
            balance = _compute_balance(customer.khata_transactions)

            if balance > 0:
                results.append({
                    "customer_id": customer.id,
                    "customer": customer.name,
                    "phone": customer.phone,
                    "balance": round(balance, 2)
                })

        results.sort(key=lambda c: c["balance"], reverse=True)

        return {
            "success": True,
            "count": len(results),
            "customers": results
        }

    finally:
        db.close()


def get_customer_ledger(customer_id):
    db = SessionLocal()

    try:
        customer = (
            db.query(Customer)
            .filter(Customer.id == customer_id)
            .first()
        )

        if not customer:
            return {
                "success": False,
                "message": "Customer not found."
            }

        transactions = (
            db.query(KhataTransaction)
            .filter(
                KhataTransaction.customer_id == customer_id
            )
            .order_by(KhataTransaction.created_at)
            .all()
        )

        ledger = []
        balance = 0

        for transaction in transactions:

            if transaction.transaction_type == "CREDIT":
                balance += transaction.amount
            else:
                balance -= transaction.amount

            ledger.append({
                "transaction_id": transaction.id,
                "type": transaction.transaction_type,
                "amount": round(transaction.amount, 2),
                "reference": transaction.reference,
                "balance": round(balance, 2),
                "created_at": str(transaction.created_at)
            })

        return {
            "success": True,
            "customer": customer.name,
            "balance": round(balance, 2),
            "ledger": ledger
        }

    finally:
        db.close()