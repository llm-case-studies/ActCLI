# Excel Legacy Workbooks

Test materials for `excel.inspect` development - public domain Excel workbooks with various complexity patterns.

## 🔒 Security Notice

**IMPORTANT**: All `.xlsm` files contain macros. Always open with macros **DISABLED**. We inspect VBA code statically; we never execute it.

## 📁 Organization

### `/macros/` - VBA-Heavy Workbooks (Preflight Focus)
- **Well_Analyses.xlsm** (USGS) - Hydrological analysis with complex VBA
- **Well_Hydrographs.xlsm** (USGS) - Water level visualization macros
- **trex_v1_5_2_webversion.xlsm** (EPA) - T-REX terrestrial exposure assessment

**Use Case**: Testing VBA Preflight risk detection, macro dependency analysis

### `/formulas/` - Formula-Heavy Workbooks (Parity Focus)
- **Nvidia_DCF.xlsx** (MIT License) - Discounted Cash Flow model with advanced formulas

**Use Case**: Testing formula parsing, dependency mapping, "all-green" Parity validation

### `/mixed/` - Mixed Complexity
- **fed_hfc_reporting_tool_v1.1.xlsm** (EPA) - HFC reporting with macros + complex formulas
- **emtool.xlsm** (EPA) - Environmental monitoring with mixed complexity
- **wirfc_covid-19_monthly_financial_impacts_on_utilities_080420.xlsm** (EPA) - Financial impact analysis

**Use Case**: End-to-end testing of complete `excel.inspect` pipeline

## 🚀 Usage with excel.inspect

```bash
# Quick formula-only validation (fast green path)
actcli excel inspect formulas/Nvidia_DCF.xlsx --mode=parity

# Full macro + formula analysis
actcli excel inspect macros/Well_Analyses.xlsm --mode=preflight --extract-vba

# Complete pipeline test
actcli excel inspect mixed/emtool.xlsm --mode=full --evidence-pack
```

## 📋 90-Second Storyline

1. **Preflight** (30s) - Scan for VBA risks, external dependencies
2. **Parity** (45s) - Validate formula calculations match Excel exactly
3. **Approve** (10s) - Generate migration recommendations
4. **Evidence Pack** (5s) - Bundle results with integrity checksums

## 📊 Expected Results

| Category | Preflight | Parity | Migration Path |
|----------|-----------|--------|----------------|
| **Formulas** | ✅ Clean | ✅ All-Green | Direct Python/R |
| **Macros** | ⚠️ VBA Risk | ⚠️ Partial | Hybrid + Manual |
| **Mixed** | ⚠️ Complex | ⚠️ Depends | Case-by-Case |

## 🔗 Source Attribution

- **USGS**: Public domain geological/hydrological analysis tools
- **EPA**: Public domain environmental assessment tools
- **MIT DCF**: MIT-licensed financial modeling example
- **State/Federal**: Various licensing (check individual files)

## 🧪 Team Integration

- **Marketing**: Use for demo storylines and success metrics
- **Biz Architect**: Reference for seminar playbooks and problem statements
- **POC Dev**: Foundation for playground tests and Phase 1 specs

---

*Perfect for validating the complete excel.inspect toolchain from risk detection to evidence-based migration!* 🚀