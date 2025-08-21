# Client Task Billing Type System

## Overview
This document explains how the billing type system works for client tasks in the TaskTempo application, including the mapping between frontend display names and database values.

## Billing Type Mapping

### Database Values → Frontend Display Names

| Database Value | Frontend Display | Description |
|----------------|------------------|-------------|
| `"fija"` | `"Mensualidad"` | Monthly subscription billing with package hours |
| `"tarifa_fija"` | `"Tarifa Fija"` | Fixed rate billing for specific tasks |
| `"hourly"` | `"Por Hora"` | Hourly billing based on time worked |

### Key Features by Billing Type

#### 1. Mensualidad (Database: "fija")
- **Purpose**: Monthly subscription billing with package hours
- **Key Fields**:
  - `asesoria_tarif`: Monthly subscription rate
  - `monthly_limit_hours_tasks`: Maximum hours included in monthly rate
  - `permanent`: Usually set to `true` for subscription clients
- **Additional Charges**: When monthly limit is exceeded, additional hours are charged at lawyer's hourly rate
- **Calculation Logic**:
  - If `total_time <= monthly_limit_hours_tasks`: Charge only `asesoria_tarif`
  - If `total_time > monthly_limit_hours_tasks`: Charge `asesoria_tarif` + additional hours × lawyer rate

#### 2. Tarifa Fija (Database: "tarifa_fija")
- **Purpose**: Fixed rate billing for specific tasks
- **Key Fields**:
  - `asesoria_tarif`: Fixed rate for the task
  - `total_value`: Total value of the task
- **Billing**: Fixed amount regardless of time spent

#### 3. Por Hora (Database: "hourly")
- **Purpose**: Hourly billing based on actual time worked
- **Key Fields**: None specific - billing is calculated from time entries
- **Calculation**: `total_time × lawyer_rate`
- **Total Value**: Dynamically calculated based on time entries

## API Request Structure

The `/client_tasks_billing` endpoint now requires date range parameters:

```json
{
  "client_id": 123,
  "start_date": "2024-01-01T00:00:00",
  "end_date": "2024-01-31T23:59:59"
}
```

## API Response Structure

The `/client_tasks_billing` endpoint now returns enhanced information for each task, filtered by the specified date range:

```json
{
  "id": 123,
  "title": "Task Title",
  "billing_type": "fija",                    // Database value
  "billing_type_display": "Mensualidad",     // Frontend display name
  "area": "Legal Area",
  "coin": "COP",
  "total_time": 25.5,                        // Hours worked
  "total_generated": 127500,                 // Value generated (for hourly tasks)
  "permanent": true,
  
  // Mensualidad specific fields
  "asesoria_tarif": 500000,                  // Monthly rate
  "monthly_limit_hours": 20,                 // Monthly hour limit
  "monthly_limit_reached": true,             // Whether limit exceeded
  "additional_hours": 5.5,                   // Hours beyond limit
  "additional_charge": 137500,               // Additional charge for excess hours
  "total_with_additional": 637500,           // Total including additional charges
  
  // Detailed breakdown of additional charges
  "additional_charges_breakdown": [
    {
      "user_id": 456,
      "user_name": "John Doe",
      "hours": 3.0,
      "rate_per_hour": 25000,
      "subtotal": 75000
    },
    {
      "user_id": 789,
      "user_name": "Jane Smith", 
      "hours": 2.5,
      "rate_per_hour": 30000,
      "subtotal": 75000
    }
  ],
  
  // Final total based on billing type
  "final_total": 637500                      // Total amount to charge
}
```

## Monthly Limit Hours Logic

### For Mensualidad Tasks (`billing_type: "fija"`)

The system now uses the `monthly_limit_hours_tasks` column from the tasks table as the primary mechanism for determining billing limits. **Note: All time calculations are now filtered by the specified date range**:

1. **Within Limit**: Only charge the monthly rate (`asesoria_tarif`)
2. **Exceeds Limit**: Charge monthly rate + additional hours at lawyer's rate
3. **Additional Hours Calculation**: 
   - Identifies time entries that exceed the monthly limit
   - Calculates charges for hours beyond the limit
   - Applies lawyer's hourly rate to excess hours
4. **No Package Hours**: The system no longer expects external package hours - all limits are defined in the task itself

### Example Scenario
- Monthly rate: $500,000 COP
- Monthly limit: 20 hours
- Actual time worked: 25.5 hours
- Excess hours: 5.5 hours
- Lawyer rate: $25,000 COP/hour
- Additional charge: 5.5 × $25,000 = $137,500 COP
- **Total**: $500,000 + $137,500 = $637,500 COP

## Database Schema

### Tasks Table Key Fields
```sql
billing_type: TEXT                    -- "fija", "tarifa_fija", "hourly"
asesoria_tarif: DECIMAL              -- Monthly rate or fixed rate
monthly_limit_hours_tasks: INTEGER   -- Monthly hour limit (for mensualidad)
total_value: DECIMAL                 -- Total task value (for tarifa fija)
permanent: BOOLEAN                   -- Whether task is permanent/subscription
```

### Time Entries Table
```sql
task_id: INTEGER                     -- Reference to task
duration: DECIMAL                    -- Hours worked
user_id: INTEGER                     -- Lawyer who worked
facturado: TEXT                      -- Billing status
```

## Usage Examples

### 1. Creating a Mensualidad Task
```python
task_data = {
    "client_id": 123,
    "title": "Monthly Legal Consultation",
    "billing_type": "fija",                    # Maps to "Mensualidad"
    "asesoria_tarif": 500000,                 # Monthly rate
    "monthly_limit_hours_tasks": 20,          # 20 hours included
    "permanent": True,                        # Subscription client
    "area": "Corporate Law"
}
```

### 2. Creating a Tarifa Fija Task
```python
task_data = {
    "client_id": 123,
    "title": "Contract Review",
    "billing_type": "tarifa_fija",            # Maps to "Tarifa Fija"
    "asesoria_tarif": 150000,                 # Fixed rate
    "total_value": 150000,                    # Total value
    "permanent": False,                       # One-time task
    "area": "Contract Law"
}
```

### 3. Creating an Hourly Task
```python
task_data = {
    "client_id": 123,
    "title": "Legal Research",
    "billing_type": "hourly",                 # Maps to "Por Hora"
    "permanent": False,                       # Time-based billing
    "area": "Research"
}
```

## Frontend Integration

When displaying billing types in the frontend, use the `billing_type_display` field for user-friendly labels:

```javascript
// Example API call with date range
const billingData = await fetch('/client_tasks_billing', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        client_id: 123,
        start_date: '2024-01-01T00:00:00',
        end_date: '2024-01-31T23:59:59'
    })
});

// Display the billing type
const billingTypeLabel = task.billing_type_display;

// Check if it's a monthly subscription
if (task.billing_type === "fija") {
    // Handle mensualidad logic
    if (task.monthly_limit_reached) {
        // Show additional charges
        console.log(`Additional hours: ${task.additional_hours}`);
        console.log(`Additional charge: ${task.additional_charge}`);
    }
}

// Get the final total to charge
const finalAmount = task.final_total;
```

## Additional Charges Calculation

### How Additional Charges Are Calculated

The system calculates additional charges using the following formula:

**Additional Charge = Σ (User Rate × Hours Worked by That User)**

**Where:**
- **User Rate** = `cost_per_hour_client` from the users table for each specific user
- **Hours Worked** = Excess hours beyond the monthly limit within the specified date range
- **Σ** = Sum of all individual user calculations

#### **Step-by-Step Process:**

1. **Identify Excess Hours**: Determine which time entries exceed the monthly limit within the date range
2. **Get User Rates**: Fetch each user's `cost_per_hour_client` from the users table
3. **Calculate Per-User Subtotals**: For each user: `excess_hours × user_tariff`
4. **Sum All Subtotals**: Additional charge = Σ (time_worked_by_user × user_tariff)

#### **Example Calculation:**

```
Monthly Limit: 20 hours
Monthly Rate: $500,000 COP

Time Entries Beyond Limit:
- User A (Rate: $25,000/h): 3 hours = $75,000
- User B (Rate: $30,000/h): 2.5 hours = $75,000

Total Additional Charge: $150,000
Final Total: $500,000 + $150,000 = $650,000
```

#### **Key Features:**

- **Individual User Rates**: Each lawyer's personal rate is applied to their hours
- **Partial Entry Handling**: If a time entry spans the limit boundary, only excess hours are charged
- **Currency Conversion**: Automatic conversion if task is in USD
- **Detailed Breakdown**: Complete breakdown of charges per user is provided
- **Accurate Calculation**: Additional charge is exactly the sum of individual user subtotals

## Date Range Filtering

The system now filters all time entries and calculations based on the specified date range:

1. **Time entries are filtered** by `start_time` between `start_date` and `end_date`
2. **Total time calculations** only include hours worked within the specified period
3. **Monthly limit checks** are based on time worked within the date range
4. **Additional charges** are calculated only for excess hours within the period
5. **Billing totals** reflect the specified time period, not all-time totals

## Simplified Billing Logic

The system now uses a simplified approach where:

1. **All billing limits are defined in the task itself** via the `monthly_limit_hours_tasks` column
2. **Date range filtering** ensures billing calculations are period-specific
3. **Automatic calculation** of additional charges when monthly limits are exceeded
4. **Clear final total** in the `final_total` field for each task

This simplifies the API and makes the system more maintainable while providing period-specific billing information.

## Migration Notes

- Existing tasks with `billing_type: "mensual"` should be updated to `"fija"`
- The system now provides both database values and display names for flexibility
- Monthly limit hours are automatically calculated and displayed from the `monthly_limit_hours_tasks` column
- Additional charges for exceeding monthly limits are automatically computed
- **Package hours logic has been removed** - all billing limits are now defined in the task's `monthly_limit_hours_tasks` column
- The `ClientTasksBillingRequest` schema no longer includes `package_hours` field
- **Date range filtering added** - the endpoint now requires `start_date` and `end_date` parameters
- All billing calculations are now period-specific based on the provided date range
