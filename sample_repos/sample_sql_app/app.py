"""Sample Python application with embedded SQL and business logic."""

import psycopg2
from datetime import datetime, timedelta


class OrderService:
    """Order processing service with business rules."""

    def __init__(self, db_connection):
        self.conn = db_connection

    def get_active_orders(self, customer_id):
        """Get active orders for a customer."""
        query = """
            SELECT order_id, order_date, total_amount, status
            FROM orders
            WHERE customer_id = %s
              AND status IN ('pending', 'processing', 'shipped')
              AND order_date >= CURRENT_DATE - INTERVAL '90 days'
            ORDER BY order_date DESC
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (customer_id,))
            return cursor.fetchall()

    def validate_order(self, order_data):
        """
        Validate order data before processing.

        Business Rules:
        - Total amount must be positive
        - Customer must exist and be active
        - All products must be available
        """
        total_amount = order_data.get('total_amount', 0)
        customer_id = order_data.get('customer_id')

        # Rule: Total amount must be at least $5
        if total_amount < 5:
            return False, "Order total must be at least $5"

        # Rule: Check customer status
        customer_query = """
            SELECT status FROM customers WHERE customer_id = %s
        """
        with self.conn.cursor() as cursor:
            cursor.execute(customer_query, (customer_id,))
            result = cursor.fetchone()

            if not result:
                return False, "Customer not found"

            if result[0] != 'active':
                return False, "Customer account is not active"

        return True, "Order validated"

    def apply_business_rules(self, order):
        """Apply business rules to order."""
        total = order['total']
        customer_id = order['customer_id']

        # Rule: Free shipping for orders over $100
        if total >= 100:
            order['shipping_cost'] = 0
        else:
            order['shipping_cost'] = 10

        # Rule: Rush processing for premium customers with orders > $200
        premium_check_query = """
            SELECT loyalty_points FROM customers WHERE customer_id = %s
        """
        with self.conn.cursor() as cursor:
            cursor.execute(premium_check_query, (customer_id,))
            result = cursor.fetchone()

            if result and result[0] >= 1000 and total > 200:
                order['processing_priority'] = 'rush'
            else:
                order['processing_priority'] = 'standard'

        return order

    def get_recommended_products(self, customer_id, limit=5):
        """Get product recommendations based on business rules."""
        # Rule: Recommend products from categories customer has purchased from
        query = """
            SELECT DISTINCT p.product_id, p.name, p.price, p.category
            FROM products p
            INNER JOIN order_items oi ON p.product_id = oi.product_id
            INNER JOIN orders o ON oi.order_id = o.order_id
            WHERE o.customer_id = %s
              AND p.is_active = true
              AND p.stock_quantity > 0
              AND p.price <= (
                  SELECT AVG(total_amount) * 1.5
                  FROM orders
                  WHERE customer_id = %s
              )
            ORDER BY o.order_date DESC
            LIMIT %s
        """
        with self.conn.cursor() as cursor:
            cursor.execute(query, (customer_id, customer_id, limit))
            return cursor.fetchall()


class InventoryService:
    """Inventory management with business rules."""

    def __init__(self, db_connection):
        self.conn = db_connection

    def check_reorder_needed(self, product_id):
        """
        Check if product needs reordering.

        Business Rule: Reorder when stock falls below 20% of average monthly sales
        """
        query = """
            SELECT
                p.stock_quantity,
                COALESCE(AVG(oi.quantity), 0) as avg_monthly_sales
            FROM products p
            LEFT JOIN order_items oi ON p.product_id = oi.product_id
            LEFT JOIN orders o ON oi.order_id = o.order_id
            WHERE p.product_id = %s
              AND o.order_date >= CURRENT_DATE - INTERVAL '90 days'
            GROUP BY p.product_id, p.stock_quantity
        """

        with self.conn.cursor() as cursor:
            cursor.execute(query, (product_id,))
            result = cursor.fetchone()

            if result:
                stock, avg_sales = result
                reorder_threshold = avg_sales * 0.2

                # Business rule: reorder if below threshold
                if stock < reorder_threshold:
                    return True, f"Stock {stock} below threshold {reorder_threshold}"

        return False, "Stock adequate"

    def get_low_stock_products(self, threshold=10):
        """Get products with low stock levels."""
        query = """
            SELECT product_id, name, stock_quantity, category
            FROM products
            WHERE stock_quantity < %s
              AND is_active = true
            ORDER BY stock_quantity ASC
        """

        with self.conn.cursor() as cursor:
            cursor.execute(query, (threshold,))
            return cursor.fetchall()


class PricingService:
    """Pricing logic with business rules."""

    def __init__(self, db_connection):
        self.conn = db_connection

    def calculate_dynamic_price(self, product_id, customer_id):
        """
        Calculate dynamic pricing based on business rules.

        Rules:
        - 10% off for premium customers
        - 5% off for bulk orders (quantity > 10)
        - Seasonal discounts
        """
        # Get base price
        query = "SELECT price FROM products WHERE product_id = %s"

        with self.conn.cursor() as cursor:
            cursor.execute(query, (product_id,))
            result = cursor.fetchone()

            if not result:
                return None

            base_price = float(result[0])
            discount_multiplier = 1.0

            # Check premium status
            premium_query = """
                SELECT loyalty_points FROM customers WHERE customer_id = %s
            """
            cursor.execute(premium_query, (customer_id,))
            loyalty_result = cursor.fetchone()

            if loyalty_result and loyalty_result[0] >= 1000:
                discount_multiplier *= 0.9  # 10% off for premium

            # Seasonal discount (example: 15% off in December)
            current_month = datetime.now().month
            if current_month == 12:
                discount_multiplier *= 0.85  # 15% holiday discount

            final_price = base_price * discount_multiplier

            # Business rule: Price cannot go below cost (assumed 50% of base)
            min_price = base_price * 0.5
            if final_price < min_price:
                final_price = min_price

            return round(final_price, 2)
