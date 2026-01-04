"""
Copiloto de Supervivencia Financiera para PYMEs
Flask application
"""
import os
import logging
from flask import Flask, render_template, request, redirect, url_for, flash, send_file, session
from werkzeug.utils import secure_filename
from functools import wraps
import pandas as pd
from io import BytesIO
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Core imports
from core.validators import validate_float, validate_file, validate_horizon, validate_granularity
from core.bank_import import parse_bank_file
from core.invoices_import import parse_sales_invoices, parse_purchase_invoices
from core.events import build_events
from core.cashflow import build_cashflow
from core.kpis import calculate_survival_metrics, enrich_kpis
from core.finance_bridge import calculate_credit_usage
from core.scenarios import generate_scenarios, compare_scenarios
from core.alerts import generate_alerts, prioritize_alerts
from core.reporting import generate_action_plan, format_action_plan_text
from core.quality import assess_data_quality
from core.prompts import build_prompt_initial, build_prompt_refined, build_rules_based_report
from core.llm_client import call_llm
from core.postcheck import postcheck_report
from core.snapshot_tools import save_snapshot, load_snapshot, update_snapshot, list_snapshots
from core.auth import (init_users_system, authenticate_user, create_user, 
                       list_all_users, update_user_status, delete_user)
from core.executive_summary import generate_executive_summary, format_scenario_changes
from core.ui_helpers import filter_cashflow_periods, aggregate_cashflow_monthly, find_alert_transactions, format_capital_breakdown

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production-2025')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Ensure data directories exist
os.makedirs('data/history', exist_ok=True)
os.makedirs('exports/templates', exist_ok=True)

# Initialize users system
init_users_system()


# Custom Jinja2 filter for markdown-like formatting
@app.template_filter('format_report')
def format_report(text):
    """Convert basic markdown to styled HTML"""
    import re
    
    if not text:
        return ""
    
    # Convert headers
    text = re.sub(r'^### (.+)$', r'<h3>\1</h3>', text, flags=re.MULTILINE)
    text = re.sub(r'^## (.+)$', r'<h2>\1</h2>', text, flags=re.MULTILINE)
    text = re.sub(r'^# (.+)$', r'<h1>\1</h1>', text, flags=re.MULTILINE)
    
    # Convert bold
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    
    # Convert italic
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    
    # Convert bullet lists
    lines = text.split('\n')
    in_list = False
    result_lines = []
    
    for line in lines:
        if line.strip().startswith('- ') or line.strip().startswith('* '):
            if not in_list:
                result_lines.append('<ul>')
                in_list = True
            item = line.strip()[2:]
            result_lines.append(f'<li>{item}</li>')
        else:
            if in_list:
                result_lines.append('</ul>')
                in_list = False
            result_lines.append(line)
    
    if in_list:
        result_lines.append('</ul>')
    
    text = '\n'.join(result_lines)
    
    # Convert paragraphs (double newline = new paragraph)
    text = re.sub(r'\n\n+', '</p><p>', text)
    text = '<p>' + text + '</p>'
    
    # Clean up empty paragraphs
    text = re.sub(r'<p>\s*</p>', '', text)
    text = re.sub(r'<p>\s*<(h[1-6]|ul|ol)>', r'<\1>', text)
    text = re.sub(r'</(h[1-6]|ul|ol)>\s*</p>', r'</\1>', text)
    
    return text


# Auth decorators
def login_required(f):
    """Decorator to require login"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Debes iniciar sesión para acceder', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            flash('Debes iniciar sesión', 'error')
            return redirect(url_for('login'))
        if session['user'].get('role') != 'admin':
            flash('Acceso denegado: requiere permisos de administrador', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function


# Auth routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = authenticate_user(username, password)
        if user:
            session['user'] = user
            flash(f'Bienvenido, {user["username"]}!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Usuario o contraseña incorrectos', 'error')
    
    return render_template('login.html')


@app.route('/logout')
def logout():
    """Logout"""
    session.pop('user', None)
    flash('Sesión cerrada correctamente', 'success')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    """Public registration page"""
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        company_name = request.form.get('company_name')
        password = request.form.get('password')
        password_confirm = request.form.get('password_confirm')
        
        # Validate
        if not all([username, email, company_name, password, password_confirm]):
            flash('Todos los campos son obligatorios', 'error')
            return render_template('register.html')
        
        if password != password_confirm:
            flash('Las contraseñas no coinciden', 'error')
            return render_template('register.html')
        
        if len(password) < 6:
            flash('La contraseña debe tener al menos 6 caracteres', 'error')
            return render_template('register.html')
        
        # Create user
        success, message = create_user(username, password, email, company_name, role='client')
        
        if success:
            flash('Cuenta creada exitosamente. Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
        else:
            flash(message, 'error')
            return render_template('register.html')
    
    return render_template('register.html')


@app.route('/')
def index():
    """Main page - redirects to login or dashboard"""
    if 'user' in session:
        return render_template('index.html')
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    """Dashboard page (alias for index)"""
    return render_template('index.html')


@app.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """Main analysis endpoint with robust error handling"""
    try:
        logger.info("=== Starting new analysis ===")
        logger.info(f"Request form keys: {list(request.form.keys())}")
        logger.info(f"Request files keys: {list(request.files.keys())}")
        
        # Ensure data directories exist
        os.makedirs('data/history', exist_ok=True)
        user_id = session.get('user', {}).get('user_id')
        if user_id:
            os.makedirs(f'data/history/{user_id}', exist_ok=True)
        
        # 1. VALIDATE INPUTS
        errors = []
        
        # Saldo actual (required)
        is_valid, error, starting_balance = validate_float(
            request.form.get('starting_balance'), 
            'Saldo actual', 
            min_value=0
        )
        if not is_valid:
            errors.append(error)
        
        # Horizonte (required)
        is_valid, error, horizon_months = validate_horizon(request.form.get('horizon_months', 6))
        if not is_valid:
            errors.append(error)
        
        # Extracto bancario (required)
        bank_file = request.files.get('bank_file')
        if not bank_file or not bank_file.filename:
            errors.append('Debes subir un extracto bancario')
        else:
            is_valid, error = validate_file(bank_file, ['.csv', '.xlsx', '.xls'])
            if not is_valid:
                errors.append(error)
        
        # Optional inputs
        is_valid, _, fixed_costs = validate_float(
            request.form.get('fixed_costs_monthly'), 
            'Gastos fijos', 
            allow_none=True
        )
        
        is_valid, _, credit_line_total = validate_float(
            request.form.get('credit_line_total'), 
            'Línea de crédito', 
            allow_none=True,
            min_value=0
        )
        credit_line_total = credit_line_total or 0.0
        
        is_valid, _, credit_line_used = validate_float(
            request.form.get('credit_line_used'), 
            'Crédito usado', 
            allow_none=True,
            min_value=0
        )
        credit_line_used = credit_line_used or 0.0
        
        is_valid, _, interest_rate = validate_float(
            request.form.get('interest_rate'), 
            'Interés', 
            allow_none=True,
            min_value=0
        )
        interest_rate = interest_rate or 0.0
        
        is_valid, _, safety_threshold = validate_float(
            request.form.get('safety_threshold'), 
            'Umbral de seguridad', 
            allow_none=True,
            min_value=0
        )
        safety_threshold = safety_threshold or 0.0
        
        is_valid, _, granularity = validate_granularity(
            request.form.get('granularity', 'weekly')
        )
        
        conservative_mode = request.form.get('conservative_mode') == 'on'
        
        # Check for errors
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('index'))
        
        # 2. PARSE FILES
        all_warnings = []
        
        # Parse bank statement (REQUIRED)
        logger.info("Parsing bank statement...")
        logger.info(f"Bank file type: {type(bank_file)}, has filename: {hasattr(bank_file, 'filename')}")
        try:
            bank_df, bank_warnings = parse_bank_file(bank_file)
            logger.info(f"Bank parsing successful: {len(bank_df)} rows")
            all_warnings.extend(bank_warnings)
            if bank_df is None or len(bank_df) == 0:
                raise ValueError("El extracto bancario está vacío o no se pudo leer")
        except Exception as e:
            logger.error(f"FATAL: Bank file parsing failed: {e}", exc_info=True)
            flash(f"Error al leer extracto bancario: {str(e)}", 'error')
            return redirect(url_for('index'))
        
        # Parse sales invoices (OPTIONAL - never break analysis)
        sales_invoices_df = None
        sales_file = request.files.get('sales_invoices_file')
        if sales_file and sales_file.filename:
            try:
                logger.info("Parsing sales invoices...")
                sales_invoices_df, sales_warnings = parse_sales_invoices(sales_file)
                all_warnings.extend(sales_warnings)
                logger.info(f"Sales invoices parsed: {len(sales_invoices_df)} rows")
            except Exception as e:
                logger.warning(f"Error parsing sales invoices (OPTIONAL): {e}")
                all_warnings.append(f"⚠️ Facturas emitidas no pudieron procesarse (continuando sin ellas)")
                sales_invoices_df = None
        
        # Parse purchase invoices (OPTIONAL - never break analysis)
        purchase_invoices_df = None
        purchase_file = request.files.get('purchase_invoices_file')
        if purchase_file and purchase_file.filename:
            try:
                logger.info("Parsing purchase invoices...")
                purchase_invoices_df, purchase_warnings = parse_purchase_invoices(purchase_file)
                all_warnings.extend(purchase_warnings)
                logger.info(f"Purchase invoices parsed: {len(purchase_invoices_df)} rows")
            except Exception as e:
                logger.warning(f"Error parsing purchase invoices (OPTIONAL): {e}")
                all_warnings.append(f"⚠️ Facturas recibidas no pudieron procesarse (continuando sin ellas)")
                purchase_invoices_df = None
        
        # 3. ASSESS DATA QUALITY
        quality_assessment = assess_data_quality(
            bank_df, 
            sales_invoices_df, 
            purchase_invoices_df,
            all_warnings
        )
        
        coverage_months = quality_assessment['coverage_months']
        confidence_level = quality_assessment['confidence_level']
        quality_metrics = quality_assessment['quality_metrics']
        
        # 4. BUILD EVENTS
        logger.info("Building cash events...")
        try:
            events = build_events(
                bank_df,
                sales_invoices_df,
                purchase_invoices_df,
                fixed_costs,
                conservative_mode
            )
            logger.info(f"Events built: {len(events)}")
        except Exception as e:
            logger.error(f"Error building events: {e}", exc_info=True)
            flash(f"Error al construir eventos de caja: {str(e)}", 'error')
            return redirect(url_for('index'))
        
        # 5. BUILD BASE CASHFLOW
        logger.info("Building cashflow...")
        try:
            cashflow_df, kpis = build_cashflow(
                events,
                starting_balance,
                horizon_months,
                granularity,
                safety_threshold
            )
            logger.info(f"Cashflow built: {len(cashflow_df)} periods")
        except Exception as e:
            logger.error(f"Error building cashflow: {e}", exc_info=True)
            flash(f"Error al proyectar cashflow: {str(e)}", 'error')
            return redirect(url_for('index'))
        
        # 6. CALCULATE SURVIVAL METRICS
        logger.info("Calculating survival metrics...")
        survival_analysis = calculate_survival_metrics(
            kpis,
            horizon_months,
            safety_threshold,
            credit_line_total,
            credit_line_used
        )
        
        # Enrich KPIs
        enriched_kpis = enrich_kpis(kpis, survival_analysis)
        
        # 7. CALCULATE CREDIT USAGE
        credit_usage = {}
        if credit_line_total > 0:
            logger.info("Calculating credit usage...")
            credit_usage = calculate_credit_usage(
                cashflow_df,
                credit_line_total,
                credit_line_used,
                interest_rate
            )
        
        # 8. GENERATE SCENARIOS
        logger.info("Generating scenarios...")
        scenarios = generate_scenarios(
            events,
            starting_balance,
            horizon_months,
            granularity,
            safety_threshold,
            credit_line_total,
            credit_line_used
        )
        
        scenarios_comparison = compare_scenarios(scenarios)
        
        # 9. GENERATE ALERTS (with quality metrics)
        logger.info("Generating alerts...")
        alerts = generate_alerts(enriched_kpis, survival_analysis, cashflow_df, 
                                quality_metrics=quality_metrics)
        alerts = prioritize_alerts(alerts)
        
        # 10. GENERATE ACTION PLAN
        logger.info("Generating action plan...")
        action_plan = generate_action_plan(alerts, enriched_kpis, survival_analysis)
        
        # 10.5 GENERATE EXECUTIVE SUMMARY (NEW!)
        logger.info("Generating executive summary...")
        executive_summary = generate_executive_summary(
            enriched_kpis, 
            survival_analysis, 
            alerts, 
            quality_metrics,
            cashflow_df
        )
        
        # 10.6 FORMAT SCENARIO CHANGES EXPLANATION (NEW!)
        has_future_data = quality_metrics.get('has_future_collections') or quality_metrics.get('has_future_payments')
        scenario_explanations = format_scenario_changes(scenarios, has_future_data)
        
        # 10.7 FORMAT CAPITAL BREAKDOWN (NEW!)
        capital_breakdown = format_capital_breakdown(survival_analysis)
        
        # 11. GENERATE REPORT (LLM or rules-based)
        logger.info("Generating report...")
        
        payload = {
            'kpis': enriched_kpis,
            'survival': survival_analysis,
            'alerts': alerts,
            'scenarios': {k: {'name': v['name'], 'kpis': v['kpis']} for k, v in scenarios.items()},
            'coverage_months': coverage_months,
            'confidence_level': confidence_level
        }
        
        prompt = build_prompt_initial(payload)
        llm_report = call_llm(prompt)
        
        if llm_report:
            # Post-check for hallucinations
            llm_report, postcheck_warnings = postcheck_report(llm_report, payload)
            all_warnings.extend(postcheck_warnings)
            report_v1 = llm_report
            report_source = 'llm'
        else:
            report_v1 = build_rules_based_report(payload)
            report_source = 'rules'
        
        # 12. SAVE SNAPSHOT
        logger.info("Saving snapshot...")
        
        snapshot_data = {
            'inputs': {
                'starting_balance': starting_balance,
                'horizon_months': horizon_months,
                'granularity': granularity,
                'safety_threshold': safety_threshold,
                'credit_line_total': credit_line_total,
                'credit_line_used': credit_line_used,
                'interest_rate': interest_rate,
                'conservative_mode': conservative_mode,
                'fixed_costs_monthly': fixed_costs
            },
            'coverage_months': coverage_months,
            'confidence_level': confidence_level,
            'quality_metrics': quality_metrics,
            'warnings': all_warnings,
            'cashflow_df': cashflow_df,
            'events_df': events_df,  # NUEVO - para drill-down
            'kpis': enriched_kpis,
            'survival': survival_analysis,
            'credit_usage': credit_usage,
            'scenarios': {k: {'name': v['name'], 'kpis': v['kpis'], 'survival': v['survival']} 
                         for k, v in scenarios.items()},
            'scenarios_comparison': scenarios_comparison,
            'scenario_explanations': scenario_explanations,  # NUEVO
            'alerts': alerts,
            'action_plan': action_plan,
            'executive_summary': executive_summary,  # NUEVO
            'capital_breakdown': capital_breakdown,  # NUEVO
            'report_v1': report_v1,
            'report_source': report_source,
            'refine_questions_presented': True,
            'refine_answers': {},
            'report_v2': None
        }
        
        user_id = session.get('user', {}).get('user_id')
        snapshot_id = save_snapshot(snapshot_data, user_id)
        
        logger.info(f"=== Analysis complete: {snapshot_id} ===")
        
        return redirect(url_for('results', snapshot_id=snapshot_id))
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger.error(f"Error in analysis: {e}", exc_info=True)
        logger.error(f"Full traceback:\n{error_details}")
        flash(f"Error en el análisis: {str(e)}", 'error')
        flash(f"Detalles: {error_details[:500]}", 'error')
        return redirect(url_for('index'))


@app.route('/results/<snapshot_id>')
@login_required
def results(snapshot_id):
    """Display results page"""
    user_id = session.get('user', {}).get('user_id')
    snapshot = load_snapshot(snapshot_id, user_id)
    
    if not snapshot:
        flash('Análisis no encontrado', 'error')
        return redirect(url_for('index'))
    
    # Prepare data for template
    cashflow_df = pd.DataFrame(snapshot['cashflow_df'])
    if len(cashflow_df) > 0:
        # Convert to datetime and then to formatted string
        # Handle both string and datetime formats
        try:
            cashflow_df['period_start'] = pd.to_datetime(cashflow_df['period_start']).dt.strftime('%Y-%m-%d')
            cashflow_df['period_end'] = pd.to_datetime(cashflow_df['period_end']).dt.strftime('%Y-%m-%d')
        except Exception as e:
            logger.warning(f"Error formatting dates: {e}")
            # If already strings, just extract first 10 chars (YYYY-MM-DD)
            cashflow_df['period_start'] = cashflow_df['period_start'].apply(lambda x: str(x)[:10] if x else '')
            cashflow_df['period_end'] = cashflow_df['period_end'].apply(lambda x: str(x)[:10] if x else '')
    
    scenarios_comparison = pd.DataFrame(snapshot['scenarios_comparison'])
    
    # Get current report (v2 if refined, else v1)
    current_report = snapshot.get('report_v2') or snapshot.get('report_v1')
    
    # Prepare events_df for drill-down (if available)
    events_df = None
    if 'events_df' in snapshot and snapshot['events_df'] is not None:
        try:
            events_df = pd.DataFrame(snapshot['events_df'])
        except:
            logger.warning("Could not load events_df for drill-down")
    
    return render_template(
        'results.html',
        snapshot=snapshot,
        cashflow=cashflow_df.to_dict('records'),
        scenarios_comparison=scenarios_comparison.to_dict('records'),
        current_report=current_report,
        events_available=events_df is not None
    )


@app.route('/refine/<snapshot_id>', methods=['POST'])
@login_required
def refine(snapshot_id):
    """Refine analysis with user answers"""
    try:
        logger.info(f"Refining analysis: {snapshot_id}")
        
        user_id = session.get('user', {}).get('user_id')
        snapshot = load_snapshot(snapshot_id, user_id)
        if not snapshot:
            flash('Análisis no encontrado', 'error')
            return redirect(url_for('index'))
        
        # Collect refine answers
        refine_answers = {
            'priorities': request.form.getlist('priorities'),
            'timing': request.form.get('timing', ''),
            'control': request.form.get('control', ''),
            'upcoming_cashflows': request.form.get('upcoming_cashflows', ''),
            'can_renegotiate': request.form.get('can_renegotiate', '')
        }
        
        # Build refined payload
        payload = {
            'kpis': snapshot['kpis'],
            'survival': snapshot['survival'],
            'alerts': snapshot['alerts'],
            'coverage_months': snapshot['coverage_months'],
            'confidence_level': snapshot['confidence_level']
        }
        
        # Generate refined report
        prompt = build_prompt_refined(payload, refine_answers)
        llm_report = call_llm(prompt)
        
        if llm_report:
            llm_report, warnings = postcheck_report(llm_report, payload)
            report_v2 = llm_report
        else:
            # Fallback: add user context to rules-based report
            report_v2 = snapshot['report_v1'] + "\n\n## Contexto Adicional\n\n"
            report_v2 += f"Prioridades: {', '.join(refine_answers['priorities'])}\n"
            report_v2 += f"Situación de cobros: {refine_answers['timing']}\n"
        
        # Update snapshot
        updates = {
            'refine_answers': refine_answers,
            'report_v2': report_v2
        }
        
        update_snapshot(snapshot_id, updates, user_id)
        
        logger.info(f"Analysis refined: {snapshot_id}")
        flash('Informe actualizado con tus respuestas', 'success')
        
        return redirect(url_for('results', snapshot_id=snapshot_id))
    
    except Exception as e:
        logger.error(f"Error refining: {e}", exc_info=True)
        flash(f"Error al refinar: {str(e)}", 'error')
        return redirect(url_for('results', snapshot_id=snapshot_id))


@app.route('/history')
@login_required
def history():
    """List all analyses"""
    user_id = session.get('user', {}).get('user_id')
    snapshots = list_snapshots(user_id)
    return render_template('history.html', snapshots=snapshots)


@app.route('/delete/<snapshot_id>', methods=['POST'])
@login_required
def delete_analysis(snapshot_id):
    """Delete analysis from history"""
    try:
        user_id = session.get('user', {}).get('user_id')
        
        # Determine file path
        if user_id:
            snapshot_file = os.path.join('data', 'history', user_id, f'{snapshot_id}.json')
            index_file = os.path.join('data', 'history', user_id, 'index.json')
        else:
            snapshot_file = os.path.join('data', 'history', f'{snapshot_id}.json')
            index_file = os.path.join('data', 'history', 'index.json')
        
        # Delete snapshot file
        if os.path.exists(snapshot_file):
            os.remove(snapshot_file)
            logger.info(f"Deleted snapshot: {snapshot_id}")
        
        # Update index
        if os.path.exists(index_file):
            with open(index_file, 'r', encoding='utf-8') as f:
                index = json.load(f)
            index['snapshots'] = [s for s in index['snapshots'] if s['snapshot_id'] != snapshot_id]
            with open(index_file, 'w', encoding='utf-8') as f:
                json.dump(index, f, indent=2, ensure_ascii=False)
        
        flash('Análisis eliminado correctamente', 'success')
    except Exception as e:
        logger.error(f"Error deleting analysis: {e}")
        flash(f'Error al eliminar análisis: {str(e)}', 'error')
    
    return redirect(url_for('history'))


@app.route('/help')
@login_required
def help_page():
    """Help page"""
    return render_template('help.html')


@app.route('/download/<snapshot_id>/<file_type>')
@login_required
def download(snapshot_id, file_type):
    """Download analysis in various formats"""
    user_id = session.get('user', {}).get('user_id')
    snapshot = load_snapshot(snapshot_id, user_id)
    
    if not snapshot:
        flash('Análisis no encontrado', 'error')
        return redirect(url_for('index'))
    
    try:
        if file_type == 'txt':
            # Generate TXT report
            report = snapshot.get('report_v2') or snapshot.get('report_v1')
            content = f"INFORME DE SUPERVIVENCIA FINANCIERA\n"
            content += f"Generado: {snapshot['created_at']}\n"
            content += f"Confianza: {snapshot['confidence_level']}\n"
            content += f"Cobertura: {snapshot['coverage_months']:.1f} meses\n"
            content += "="*60 + "\n\n"
            content += report
            
            buffer = BytesIO(content.encode('utf-8'))
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='text/plain',
                as_attachment=True,
                download_name=f'informe_{snapshot_id}.txt'
            )
        
        elif file_type == 'md':
            # Generate Markdown report
            report = snapshot.get('report_v2') or snapshot.get('report_v1')
            content = f"# Informe de Supervivencia Financiera\n\n"
            content += f"**Generado:** {snapshot['created_at']}  \n"
            content += f"**Confianza:** {snapshot['confidence_level']}  \n"
            content += f"**Cobertura:** {snapshot['coverage_months']:.1f} meses\n\n"
            content += "---\n\n"
            content += report
            
            buffer = BytesIO(content.encode('utf-8'))
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='text/markdown',
                as_attachment=True,
                download_name=f'informe_{snapshot_id}.md'
            )
        
        elif file_type == 'csv_cashflow':
            # Export cashflow as CSV
            cashflow_df = pd.DataFrame(snapshot['cashflow_df'])
            buffer = BytesIO()
            cashflow_df.to_csv(buffer, index=False, encoding='utf-8')
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'cashflow_{snapshot_id}.csv'
            )
        
        elif file_type == 'csv_scenarios':
            # Export scenarios comparison as CSV
            scenarios_df = pd.DataFrame(snapshot['scenarios_comparison'])
            buffer = BytesIO()
            scenarios_df.to_csv(buffer, index=False, encoding='utf-8')
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'escenarios_{snapshot_id}.csv'
            )
        
        else:
            flash('Formato no soportado', 'error')
            return redirect(url_for('results', snapshot_id=snapshot_id))
    
    except Exception as e:
        logger.error(f"Error generating download: {e}")
        flash(f"Error al generar descarga: {str(e)}", 'error')
        return redirect(url_for('results', snapshot_id=snapshot_id))


# Admin routes
@app.route('/admin')
@admin_required
def admin_panel():
    """Admin panel"""
    users = list_all_users()
    return render_template('admin.html', users=users)


@app.route('/admin/create_user', methods=['POST'])
@admin_required
def admin_create_user():
    """Create new user"""
    username = request.form.get('username')
    email = request.form.get('email')
    company_name = request.form.get('company_name')
    password = request.form.get('password')
    
    success, message = create_user(username, password, email, company_name)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/toggle_user/<user_id>', methods=['POST'])
@admin_required
def admin_toggle_user(user_id):
    """Toggle user active status"""
    from core.auth import get_user_by_id
    user = get_user_by_id(user_id)
    
    if user:
        new_status = not user.get('active', True)
        success, message = update_user_status(user_id, new_status)
        flash(message, 'success' if success else 'error')
    else:
        flash('Usuario no encontrado', 'error')
    
    return redirect(url_for('admin_panel'))


@app.route('/admin/delete_user/<user_id>', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    """Delete user"""
    success, message = delete_user(user_id)
    flash(message, 'success' if success else 'error')
    return redirect(url_for('admin_panel'))


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting Copiloto de Supervivencia Financiera on port {port}")
    logger.info(f"Debug mode: {debug}")
    
    # Run with verbose error output
    app.run(host='0.0.0.0', port=port, debug=debug, use_reloader=False, threaded=True)
