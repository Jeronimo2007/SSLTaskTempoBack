-- Eliminar la vista existente
DROP VIEW IF EXISTS group_permanent_summary;

-- Crear la nueva vista para grupos permanentes
CREATE VIEW group_permanent_summary AS
SELECT 
    g.group_name AS client,
    g.monthly_limit_hours AS monthly_hours,
    COALESCE(SUM(t.current_month_hours), 0) AS current_month_hours
FROM clients c
JOIN groups_tasks gt ON gt.client_id = c.id
JOIN groups g ON g.id = gt.group_id
JOIN tasks t ON t.id = gt.task_id
WHERE t.permanent = TRUE
GROUP BY g.group_name, g.monthly_limit_hours, g.id
ORDER BY g.group_name, g.id; 