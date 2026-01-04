"""
Test direct analysis to find the error
"""
import sys
import traceback
from core.bank_import import parse_bank_file
from core.invoices_import import parse_sales_invoices, parse_purchase_invoices
from core.events import build_events
from core.cashflow import build_cashflow
from core.kpis import calculate_survival_metrics, enrich_kpis
from core.quality import assess_data_quality
from core.scenarios import generate_scenarios, compare_scenarios
from core.alerts import generate_alerts, prioritize_alerts
from core.reporting import generate_action_plan
from core.prompts import build_prompt_initial, build_rules_based_report
from core.llm_client import call_llm
from core.postcheck import postcheck_report
from core.snapshot_tools import save_snapshot

print("="*60)
print("Testing analysis flow step by step")
print("="*60)

try:
    # Test parameters
    starting_balance = 38500.0
    horizon_months = 6
    granularity = 'weekly'
    safety_threshold = 10000.0
    fixed_costs = 5000.0
    
    print("\n1. Opening bank file...")
    with open('exports/templates/bank_statement_template.csv', 'rb') as f:
        bank_df, bank_warnings = parse_bank_file(f)
    print(f"   ✓ Bank: {len(bank_df)} transactions")
    
    print("\n2. Opening sales invoices...")
    with open('exports/templates/invoices_sales_template.csv', 'rb') as f:
        sales_df, sales_warnings = parse_sales_invoices(f)
    print(f"   ✓ Sales: {len(sales_df)} invoices")
    
    print("\n3. Opening purchase invoices...")
    with open('exports/templates/invoices_purchase_template.csv', 'rb') as f:
        purchase_df, purchase_warnings = parse_purchase_invoices(f)
    print(f"   ✓ Purchases: {len(purchase_df)} invoices")
    
    print("\n4. Assessing data quality...")
    quality = assess_data_quality(bank_df, sales_df, purchase_df, [])
    print(f"   ✓ Coverage: {quality['coverage_months']:.1f} months")
    print(f"   ✓ Confidence: {quality['confidence_level']}")
    
    print("\n5. Building events...")
    events = build_events(bank_df, sales_df, purchase_df, fixed_costs, False)
    print(f"   ✓ Events: {len(events)}")
    
    print("\n6. Building cashflow...")
    cashflow_df, kpis = build_cashflow(events, starting_balance, horizon_months, granularity, safety_threshold)
    print(f"   ✓ Cashflow: {len(cashflow_df)} periods")
    print(f"   ✓ Min balance: {kpis.get('min_balance', 'N/A')}")
    
    print("\n7. Calculating survival metrics...")
    survival = calculate_survival_metrics(kpis, horizon_months, safety_threshold, 50000, 10000)
    print(f"   ✓ Survival analyzed")
    
    print("\n8. Enriching KPIs...")
    enriched_kpis = enrich_kpis(kpis, survival)
    print(f"   ✓ KPIs enriched")
    
    print("\n9. Generating scenarios...")
    scenarios = generate_scenarios(events, starting_balance, horizon_months, granularity, safety_threshold, 50000, 10000)
    scenarios_comparison = compare_scenarios(scenarios)
    print(f"   ✓ Scenarios: {len(scenarios)}")
    
    print("\n10. Generating alerts...")
    alerts = generate_alerts(enriched_kpis, survival, cashflow_df, quality_metrics=quality['quality_metrics'])
    alerts = prioritize_alerts(alerts)
    print(f"   ✓ Alerts: {len(alerts)}")
    
    print("\n11. Generating action plan...")
    action_plan = generate_action_plan(alerts, enriched_kpis, survival)
    print(f"   ✓ Action plan generated")
    
    print("\n12. Building prompt...")
    payload = {
        'kpis': enriched_kpis,
        'survival': survival,
        'alerts': alerts,
        'scenarios': {k: {'name': v['name'], 'kpis': v['kpis']} for k, v in scenarios.items()},
        'coverage_months': quality['coverage_months'],
        'confidence_level': quality['confidence_level']
    }
    prompt = build_prompt_initial(payload)
    print(f"   ✓ Prompt built: {len(prompt)} chars")
    
    print("\n13. Generating report (rules-based)...")
    report = build_rules_based_report(payload)
    print(f"   ✓ Report: {len(report)} chars")
    
    print("\n14. Preparing snapshot data...")
    snapshot_data = {
        'inputs': {
            'starting_balance': starting_balance,
            'horizon_months': horizon_months,
            'granularity': granularity,
            'safety_threshold': safety_threshold,
            'credit_line_total': 50000.0,
            'credit_line_used': 10000.0,
            'interest_rate': 6.5,
            'conservative_mode': False,
            'fixed_costs_monthly': fixed_costs
        },
        'coverage_months': quality['coverage_months'],
        'confidence_level': quality['confidence_level'],
        'quality_metrics': quality['quality_metrics'],
        'warnings': [],
        'cashflow_df': cashflow_df,
        'kpis': enriched_kpis,
        'survival': survival,
        'credit_usage': {},
        'scenarios': {k: {'name': v['name'], 'kpis': v['kpis'], 'survival': v['survival']} 
                     for k, v in scenarios.items()},
        'scenarios_comparison': scenarios_comparison,
        'alerts': alerts,
        'action_plan': action_plan,
        'report_v1': report,
        'report_source': 'rules',
        'refine_questions_presented': True,
        'refine_answers': {},
        'report_v2': None
    }
    print(f"   ✓ Snapshot data prepared")
    
    print("\n15. Saving snapshot...")
    snapshot_id = save_snapshot(snapshot_data, 'test_user')
    print(f"   ✓ Snapshot saved: {snapshot_id}")
    
    print("\n" + "="*60)
    print("✓ ALL TESTS PASSED!")
    print("="*60)
    
except Exception as e:
    print("\n" + "="*60)
    print("✗ ERROR FOUND:")
    print("="*60)
    print(f"\nError: {e}")
    print(f"\nType: {type(e).__name__}")
    print("\nFull traceback:")
    traceback.print_exc()
    print("="*60)
