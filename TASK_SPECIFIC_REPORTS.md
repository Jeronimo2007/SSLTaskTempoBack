# Task-Specific Reports in Comprehensive Report API

## Overview
The comprehensive report API now supports task-specific reports when a `task_id` is provided. This allows you to generate reports for individual tasks in the format that corresponds to their billing type.

## API Endpoint
```
POST /reports/comprehensive_report
```

## Request Schema
```json
{
  "report_type": "general|tarifa_fija|mensualidad|hourly",
  "start_date": "2024-01-01T00:00:00",  // Optional, defaults to current month
  "end_date": "2024-01-31T23:59:59",    // Optional, defaults to current month
  "client_id": 123,                      // Optional, defaults to all clients
  "task_id": 456                         // NEW: Optional, if provided returns task-specific report
}
```

## Task-Specific Report Behavior

When `task_id` is provided, the API automatically detects the task's billing type and returns a report in the appropriate format:

### 1. Hourly Billing Tasks (`billing_type: "hourly"`)
- **Format**: Time tracking with hourly rates
- **Columns**: Abogado, Rol, Cliente, Asunto, Trabajo, Área, Fecha Trabajo, Modo de Facturación, Tiempo Trabajado, Tarifa Horaria, Moneda, Total, Facturado
- **Calculation**: Total = Hours × Hourly Rate
- **Summary**: Includes total hours and total value

### 2. Fixed Rate Tasks (`billing_type: "tarifa_fija"`)
- **Format**: Fixed rate billing
- **Columns**: Abogado, Rol, Cliente, Asunto, Trabajo, Área, Fecha Trabajo, Modo de Facturación, Tiempo Trabajado, Tarifa Fija, Moneda, Total, Facturado
- **Calculation**: Total = Fixed Rate (same for all entries)
- **Summary**: Shows total hours worked and fixed rate amount

### 3. Monthly Subscription Tasks (`billing_type: "fija"`)
- **Format**: Monthly subscription with hour limits
- **Columns**: Abogado, Rol, Cliente, Asunto, Trabajo, Área, Fecha Trabajo, Modo de Facturación, Tiempo Trabajado, Límite Mensual, Tarifa Mensual, Moneda, Total, Facturado
- **Calculation**: Monthly rate + additional charges for excess hours
- **Summary**: Includes monthly rate and any additional charges

### 4. Other Billing Types
- **Format**: General format as fallback
- **Columns**: Standard comprehensive report columns
- **Calculation**: Hourly rate × time for each entry

## Example Usage

### Generate Task-Specific Report
```bash
curl -X POST "http://localhost:8000/reports/comprehensive_report" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "report_type": "general",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-31T23:59:59",
    "task_id": 123
  }'
```

### Generate Comprehensive Report (Existing Behavior)
```bash
curl -X POST "http://localhost:8000/reports/comprehensive_report" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "report_type": "hourly",
    "start_date": "2024-01-01T00:00:00",
    "end_date": "2024-01-31T23:59:59"
  }'
```

## Benefits

1. **Consistent Formatting**: Each task gets a report in the format that matches its billing type
2. **Detailed Analysis**: Focus on specific tasks with relevant information
3. **Flexible Reporting**: Can still generate comprehensive reports when needed
4. **Backward Compatibility**: Existing API calls continue to work unchanged

## Notes

- The `report_type` parameter is still required but its value determines the fallback format for unknown billing types
- Task-specific reports automatically include summary rows with totals
- All reports maintain the same Excel output format for consistency
- Date filtering applies to time entries within the specified range
