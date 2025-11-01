-- Stored procedures and functions for business logic

-- Calculate discount based on order total
CREATE OR REPLACE FUNCTION calc_discount(total NUMERIC) RETURNS NUMERIC AS $$
BEGIN
  -- Business Rule: Tiered discount based on order value
  IF total > 1000 THEN
    RETURN total * 0.1;  -- 10% discount for orders over $1000
  ELSIF total > 500 THEN
    RETURN total * 0.05; -- 5% discount for orders over $500
  ELSE
    RETURN 0;            -- No discount for smaller orders
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Check customer eligibility for premium features
CREATE OR REPLACE FUNCTION is_eligible_for_premium(
  customer_id_param INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
  customer_loyalty_points INTEGER;
  registration_months INTEGER;
  order_count INTEGER;
BEGIN
  -- Get customer information
  SELECT
    loyalty_points,
    EXTRACT(MONTH FROM AGE(CURRENT_DATE, registration_date))
  INTO customer_loyalty_points, registration_months
  FROM customers
  WHERE customer_id = customer_id_param;

  -- Count orders
  SELECT COUNT(*) INTO order_count
  FROM orders
  WHERE customer_id = customer_id_param
    AND status = 'delivered';

  -- Business Rules for Premium Eligibility:
  -- 1. Customer must have at least 1000 loyalty points
  -- 2. OR customer must be registered for at least 12 months AND have 5+ orders
  IF customer_loyalty_points >= 1000 THEN
    RETURN true;
  ELSIF registration_months >= 12 AND order_count >= 5 THEN
    RETURN true;
  ELSE
    RETURN false;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Apply automatic order status updates
CREATE OR REPLACE FUNCTION update_order_status() RETURNS TRIGGER AS $$
BEGIN
  -- Business Rule: Auto-cancel orders not processed within 7 days
  IF NEW.status = 'pending'
     AND AGE(CURRENT_TIMESTAMP, NEW.order_date) > INTERVAL '7 days' THEN
    NEW.status := 'cancelled';
  END IF;

  -- Business Rule: Auto-complete delivered orders after 30 days
  IF NEW.status = 'delivered'
     AND AGE(CURRENT_TIMESTAMP, NEW.order_date) > INTERVAL '30 days' THEN
    -- Mark as completed (would update in a real system)
    NULL;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER order_status_check
  BEFORE UPDATE ON orders
  FOR EACH ROW
  EXECUTE FUNCTION update_order_status();

-- Calculate loyalty points for an order
CREATE OR REPLACE FUNCTION calculate_loyalty_points(
  order_amount NUMERIC
) RETURNS INTEGER AS $$
BEGIN
  -- Business Rule: 1 point per $10 spent, bonus points for large orders
  IF order_amount >= 500 THEN
    RETURN FLOOR(order_amount / 10) * 2;  -- Double points for orders >= $500
  ELSE
    RETURN FLOOR(order_amount / 10);      -- Standard rate
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Validate product availability
CREATE OR REPLACE FUNCTION check_product_availability(
  product_id_param INTEGER,
  requested_quantity INTEGER
) RETURNS BOOLEAN AS $$
DECLARE
  available_stock INTEGER;
  product_active BOOLEAN;
BEGIN
  SELECT stock_quantity, is_active
  INTO available_stock, product_active
  FROM products
  WHERE product_id = product_id_param;

  -- Business Rules:
  -- 1. Product must be active
  -- 2. Sufficient stock must be available
  -- 3. Minimum order quantity is 1, maximum is 100
  IF NOT product_active THEN
    RETURN false;
  ELSIF available_stock < requested_quantity THEN
    RETURN false;
  ELSIF requested_quantity < 1 OR requested_quantity > 100 THEN
    RETURN false;
  ELSE
    RETURN true;
  END IF;
END;
$$ LANGUAGE plpgsql;

-- Calculate final order amount with business rules
CREATE OR REPLACE FUNCTION calculate_final_amount(
  subtotal NUMERIC,
  customer_id_param INTEGER,
  promo_code VARCHAR DEFAULT NULL
) RETURNS NUMERIC AS $$
DECLARE
  discount_amount NUMERIC := 0;
  is_premium BOOLEAN;
  tax_rate NUMERIC := 0.08;  -- 8% tax
  final_total NUMERIC;
BEGIN
  -- Check premium status
  is_premium := is_eligible_for_premium(customer_id_param);

  -- Apply automatic discount
  discount_amount := calc_discount(subtotal);

  -- Business Rule: Premium customers get additional 5% off
  IF is_premium THEN
    discount_amount := discount_amount + (subtotal * 0.05);
  END IF;

  -- Business Rule: Promo codes give fixed $20 off
  IF promo_code IS NOT NULL AND promo_code != '' THEN
    discount_amount := discount_amount + 20;
  END IF;

  -- Business Rule: Discount cannot exceed 50% of subtotal
  IF discount_amount > (subtotal * 0.5) THEN
    discount_amount := subtotal * 0.5;
  END IF;

  -- Calculate final amount with tax
  final_total := (subtotal - discount_amount) * (1 + tax_rate);

  -- Business Rule: Minimum order amount is $5 after all discounts
  IF final_total < 5 THEN
    final_total := 5;
  END IF;

  RETURN final_total;
END;
$$ LANGUAGE plpgsql;
