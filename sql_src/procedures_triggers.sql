USE Meal_Manufacturer;

DROP PROCEDURE IF EXISTS RecordProductionBatch;
DELIMITER //

CREATE PROCEDURE RecordProductionBatch(
    IN p_batch_number      VARCHAR(100),
    IN p_product_id        INT,
    IN p_plan_id           INT,
    IN p_quantity_produced INT,
    IN p_production_date   DATE,
    IN p_expiration_date   DATE,
    OUT p_total_cost       DECIMAL(12,2),
    OUT p_cost_per_unit    DECIMAL(12,2),
    OUT p_success          BOOLEAN
)
BEGIN
    -- 1) Variable declarations
    DECLARE v_total_cost         DECIMAL(12,2) DEFAULT 0;
    DECLARE v_cost_per_unit      DECIMAL(12,2) DEFAULT 0;
    DECLARE done                 INT           DEFAULT FALSE;
    DECLARE v_lot_number         VARCHAR(100);
    DECLARE v_quantity_used      DECIMAL(10,2);
    DECLARE v_cost_per_unit_lot  DECIMAL(10,2);
    DECLARE v_lot_cost           DECIMAL(12,2);

    -- 2) Cursor declaration
    DECLARE cur_consumption CURSOR FOR
        SELECT ingredient_lot_number, quantity_used
        FROM Batch_Consumption
        WHERE product_batch_number = p_batch_number;

    -- 3) Handlers
    -- When cursor has no more rows
    DECLARE CONTINUE HANDLER FOR NOT FOUND
        SET done = TRUE;

    -- On any SQL exception: rollback and flag failure
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        SET p_success = FALSE;
        RESIGNAL;
    END;

    -- 4) Main procedure logic
    START TRANSACTION;

    -- Calculate total cost from consumption records
    OPEN cur_consumption;
    read_loop: LOOP
        FETCH cur_consumption INTO v_lot_number, v_quantity_used;
        IF done THEN
            LEAVE read_loop;
        END IF;

        -- Get cost per unit for this lot
        SELECT cost_per_unit
        INTO   v_cost_per_unit_lot
        FROM   Ingredient_Batches
        WHERE  lot_number = v_lot_number;

        SET v_lot_cost   = v_quantity_used * v_cost_per_unit_lot;
        SET v_total_cost = v_total_cost + v_lot_cost;

        -- Update lot quantity
        UPDATE Ingredient_Batches
        SET    quantity_on_hand = quantity_on_hand - v_quantity_used
        WHERE  lot_number = v_lot_number;

        -- Validate quantity (cannot go below zero)
        IF (SELECT quantity_on_hand
            FROM   Ingredient_Batches
            WHERE  lot_number = v_lot_number) < 0 THEN
            SIGNAL SQLSTATE '45000'
                SET MESSAGE_TEXT = 'Insufficient quantity in lot';
        END IF;
    END LOOP;
    CLOSE cur_consumption;

    -- Compute cost per unit
    IF p_quantity_produced > 0 THEN
        SET v_cost_per_unit = v_total_cost / p_quantity_produced;
    END IF;

    -- Insert product batch row
    INSERT INTO Product_Batches (
        batch_number, product_id, plan_id, quantity_produced,
        total_cost, cost_per_unit, production_date, expiration_date
    ) VALUES (
        p_batch_number, p_product_id, p_plan_id, p_quantity_produced,
        v_total_cost, v_cost_per_unit, p_production_date, p_expiration_date
    );

    -- Set OUT parameters
    SET p_total_cost    = v_total_cost;
    SET p_cost_per_unit = v_cost_per_unit;
    SET p_success       = TRUE;

    COMMIT;
END//
DELIMITER ;
