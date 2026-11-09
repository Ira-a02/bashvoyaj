-- ==========================================
-- SQL-запросы для базы данных туристического агентства
-- ==========================================

-- 1. Выборка активных туров длительностью более 2 дней
SELECT name, description_short, time_of_tour
FROM Tours
WHERE is_active = TRUE AND time_of_tour > 2
ORDER BY time_of_tour DESC;


-- 2. Вывод всех активных заказов с названием тура и именем менеджера
SELECT 
    o.id AS order_id, 
    o.order_date, 
    t.name AS tour_name, 
    m.name AS manager_name, 
    o.total_cost
FROM Orders o
JOIN Tours t ON o.tour_id = t.id
LEFT JOIN Managers m ON o.manager_id = m.id
WHERE o.is_active = TRUE;


-- 3. Подсчет выручки и количества заказов для каждого менеджера
SELECT 
    m.name AS manager_name, 
    COUNT(o.id) AS total_orders, 
    SUM(o.total_cost) AS total_revenue
FROM Managers m
JOIN Orders o ON m.id = o.manager_id
WHERE o.is_active = TRUE
GROUP BY m.name
ORDER BY total_revenue DESC;


-- 4. Поиск туров, на которые было оформлено больше 5 заказов
SELECT 
    t.name AS tour_name, 
    COUNT(o.id) AS orders_count
FROM Tours t
JOIN Orders o ON t.id = o.tour_id
WHERE o.is_active = TRUE
GROUP BY t.name
HAVING COUNT(o.id) > 5;


-- 5. Ранжирование туров по общей сумме выручки
SELECT 
    t.name AS tour_name, 
    SUM(o.total_cost) AS revenue,
    RANK() OVER (ORDER BY SUM(o.total_cost) DESC) AS revenue_rank
FROM Tours t
JOIN Orders o ON t.id = o.tour_id
WHERE o.is_active = TRUE
GROUP BY t.name;
