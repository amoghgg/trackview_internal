# 🔑 Lockview Key Remarks Reference

## The 7-8 Important Status Indicators

These are the critical messages that determine the lock/unlock status of vehicles in the Lockview system.

---

## 🔒 LOCKED Status (2 Indicators)

### 1. "Close Shackle Auto Seal"
- **Meaning**: Lock automatically sealed/closed
- **Action**: Vehicle is secured
- **Frequency**: High - occurs at end of operations

### 2. "Shackle Closed"
- **Meaning**: Lock shackle manually or automatically closed
- **Action**: Vehicle is secured
- **Frequency**: Medium - manual confirmation

---

## 🔓 UNLOCKED Status (6 Indicators)

### 1. "Shackle Opened" / "Shackle Opned"
- **Meaning**: Lock shackle is open
- **Note**: "Opned" is a typo in the tracking system data
- **Action**: Vehicle is accessible
- **Frequency**: Very High - most common unlock indicator

### 2. "Dynamic Password Unseal"
- **Meaning**: Lock opened using dynamic password authentication
- **Action**: Temporary access granted via password
- **Security**: High - requires authorized password

### 3. "Platform Unseal"
- **Meaning**: Lock opened via web/mobile platform command
- **Action**: Remote unlock initiated
- **Frequency**: High - common for authorized access

### 4. "SMS Unseal"
- **Meaning**: Lock opened via SMS command
- **Action**: Remote unlock via text message
- **Frequency**: Medium - alternative remote access method

### 5. "Swipe Card to Unseal"
- **Meaning**: Lock opened using RFID/swipe card
- **Action**: Physical card access
- **Security**: Medium - requires physical card
- **Note**: Sometimes appears as "Swipe card to unseal successfully"

---

## 📊 Status Determination Logic

### How the System Works:

```
For each vehicle log entry:
1. Check if Message contains any LOCKED indicator
   → If yes: Status = "Locked"
   
2. Check if Message contains any UNLOCKED indicator
   → If yes: Status = "Unlocked"
   
3. If no match found
   → Status = "Unknown"
```

### For Dashboard Display:

```
Status (15-20th):
- Get all logs between 15th-20th
- Take the MOST RECENT log
- Display that log's status

Status (21st):
- Get all logs on 21st
- Take the MOST RECENT log
- Display that log's status
```

---

## 📈 Your Current Data Statistics

Based on your uploaded file (`final_imz_report.csv`):

### Updated Status Breakdown:

**Using Correct Remarks:**
- **Status (15-20th)**: 197 Locked, 22 Unlocked, 18 No Data
- **Status (21st)**: 197 Locked, 4 Unlocked, 36 No Data

**Previous (Incorrect Remarks):**
- Status (15-20th): 219 Locked, 2 Unlocked
- Status (21st): 198 Locked, 38 Unlocked

### Why the Difference?

The correct remarks categorize more events as "Unlocked" because:
- "Swipe card to unseal" was previously counted as LOCKED
- Now correctly identified as UNLOCKED
- More accurate representation of actual vehicle access patterns

---

## 🎯 Message Pattern Examples

### Real Examples from Your Data:

#### LOCKED Messages:
```
"Close Shackle Auto Sealed"  ← Auto-locked
"Shackle Closed"             ← Manually confirmed locked
```

#### UNLOCKED Messages:
```
"Shakle Opned"                          ← Most common (typo in system)
"Shackle Opened"                        ← Correct spelling version
"Swipe card to unseal successfully"     ← Card access
"Platform unseal successful"            ← Remote platform unlock
"Dynamic password unseal successful"    ← Password unlock
"SMS unseal successful"                 ← SMS unlock
```

---

## 🔧 How to Update Remarks

If you need to add or modify the status indicators:

1. Open `lockview_converter.py`
2. Find the `__init__` method (around line 10-20)
3. Modify the lists:

```python
# LOCKED indicators
self.lock_indicators = [
    "Close Shackle Auto Seal",
    "Shackle Closed",
    "Your New Locked Indicator Here"  # Add new ones
]

# UNLOCKED indicators
self.unlock_indicators = [
    "Shackle Opened",
    "Shackle Opned",
    "Dynamic password unseal",
    "Platform unseal",
    "SMS unseal",
    "Swipe card to unseal",
    "Your New Unlocked Indicator Here"  # Add new ones
]
```

4. Save the file
5. Run: `python lockview_converter.py`
6. Refresh your dashboard

---

## 📋 Case Sensitivity Note

The system uses **case-insensitive matching**, so these are all treated the same:
- "Shackle Opened"
- "shackle opened"
- "SHACKLE OPENED"
- "ShAcKlE oPeNeD"

This ensures reliable detection even if the tracking system changes capitalization.

---

## 🎨 Dashboard Display

### Color Coding:
- 🟢 **Green Badge** = Locked (Vehicle secured)
- 🔴 **Red Badge** = Unlocked (Vehicle accessible)
- 🟡 **Yellow Badge** = No Data (No logs for period)
- ⚪ **Gray Badge** = Unknown (Message not recognized)

### What Managers See:

```
Vehicle ID | Center | Status (15-20) | Status (21) | Location
TVS-1-001  | 2601   | 🟢 Locked     | 🟢 Locked   | Puri, Odisha
TVS-1-002  | 102    | 🔴 Unlocked   | 🟢 Locked   | Angul, Odisha
TVS-1-003  | 2403   | 🟢 Locked     | 🔴 Unlocked | Nayagarh, Odisha
```

---

## ⚠️ Important Notes

### Typos in Data:
- "Shakle Opned" (common typo) is handled automatically
- System recognizes both correct and typo versions

### Multiple Messages:
- Some vehicles have multiple unlock methods in same period
- Dashboard shows status from MOST RECENT log entry
- Full log history preserved in JSON file

### Missing Data:
- If no logs exist for a period → "No Data"
- If message doesn't match any indicator → "Unknown"

---

## 📞 Quick Reference Summary

**Total Indicators**: 8 (2 Locked + 6 Unlocked)

**LOCKED (2):**
1. Close Shackle Auto Seal
2. Shackle Closed

**UNLOCKED (6):**
1. Shackle Opened/Opned
2. Dynamic password unseal
3. Platform unseal
4. SMS unseal
5. Swipe card to unseal
6. (All variations with "successful" suffix)

**Your Data**: 237 vehicles, 2,132 logs, Jan 15-21 2026

---

**Last Updated**: February 3, 2026
**Data Source**: final_imz_report.csv
**System Version**: Lockview Dashboard v1.1
