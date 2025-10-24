"""
Main Flask Application
"""

import json
import csv
import io
import os
import glob
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file
from flask_jwt_extended import JWTManager, create_access_token, get_jwt_identity
from flask_cors import CORS

from config import config
from database import db
from auth import token_required, validate_login

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = config.SECRET_KEY
app.config['JWT_SECRET_KEY'] = config.JWT_SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=config.JWT_ACCESS_TOKEN_EXPIRES)

# Initialize extensions
jwt = JWTManager(app)
CORS(app, origins=config.CORS_ORIGINS)

# Validate configuration
config_errors = config.validate()
if config_errors:
    print("❌ Configuration errors:")
    for error in config_errors:
        print(f"  - {error}")
    if not config.DEBUG:
        exit(1)


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.route('/api/auth/login', methods=['POST'])
def login():
    """User login endpoint"""
    data = request.get_json()

    if not data or 'username' not in data or 'password' not in data:
        return jsonify({'error': 'Username and password required'}), 400

    username = data['username']
    password = data['password']

    # Validate credentials
    if not validate_login(username, password):
        return jsonify({'error': 'Invalid username or password'}), 401

    # Update last login
    db.update_last_login(username)

    # Create JWT token
    access_token = create_access_token(identity=username)

    return jsonify({
        'access_token': access_token,
        'username': username,
        'expires_in': config.JWT_ACCESS_TOKEN_EXPIRES
    }), 200


@app.route('/api/auth/verify', methods=['GET'])
@token_required
def verify_token(current_user):
    """Verify if token is still valid"""
    return jsonify({
        'valid': True,
        'username': current_user
    }), 200


# ============================================================================
# Search Endpoints
# ============================================================================

@app.route('/api/search', methods=['GET'])
@token_required
def search(current_user):
    """Search QA pairs with filters"""

    # Get query parameters
    query = request.args.get('q', '').strip()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    emotion = request.args.get('emotion')
    conversation_id = request.args.get('conversation_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', config.RESULTS_PER_PAGE, type=int), config.MAX_RESULTS_PER_PAGE)

    # Validate page number
    if page < 1:
        page = 1

    # Perform search
    try:
        results, total_count = db.search_qa_pairs(
            query=query if query else None,
            date_from=date_from,
            date_to=date_to,
            emotion_tone=emotion,
            conversation_id=conversation_id,
            page=page,
            per_page=per_page
        )

        total_pages = (total_count + per_page - 1) // per_page

        return jsonify({
            'results': results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_results': total_count,
                'total_pages': total_pages
            },
            'query': {
                'q': query,
                'date_from': date_from,
                'date_to': date_to,
                'emotion': emotion,
                'conversation_id': conversation_id
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Search failed', 'message': str(e)}), 500


@app.route('/api/qa/<int:qa_id>', methods=['GET'])
@token_required
def get_qa_pair(current_user, qa_id):
    """Get single QA pair with full context"""
    try:
        qa_pair = db.get_qa_pair_by_id(qa_id)

        if not qa_pair:
            return jsonify({'error': 'QA pair not found'}), 404

        # Get topics for the conversation
        topics = db.get_topics_by_conversation(qa_pair.get('conversation_id'))
        qa_pair['topics'] = topics

        return jsonify(qa_pair), 200

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve QA pair', 'message': str(e)}), 500


# ============================================================================
# Filter Endpoints
# ============================================================================

@app.route('/api/filters', methods=['GET'])
@token_required
def get_filters(current_user):
    """Get available filter options"""
    try:
        emotions = db.get_available_emotions()
        date_range = db.get_date_range()
        conversations = db.get_conversations_list()

        return jsonify({
            'emotions': emotions,
            'date_range': date_range,
            'conversations': conversations
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve filters', 'message': str(e)}), 500


@app.route('/api/conversations', methods=['GET'])
@token_required
def get_conversations(current_user):
    """Get list of all conversations"""
    try:
        conversations = db.get_conversations_list()
        return jsonify(conversations), 200

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve conversations', 'message': str(e)}), 500


# ============================================================================
# Export Endpoints
# ============================================================================

@app.route('/api/export', methods=['GET'])
@token_required
def export_results(current_user):
    """Export search results as CSV or JSON"""

    # Get same query parameters as search
    query = request.args.get('q', '').strip()
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    emotion = request.args.get('emotion')
    conversation_id = request.args.get('conversation_id', type=int)
    export_format = request.args.get('format', 'csv').lower()

    # Get all results (no pagination)
    try:
        results, _ = db.search_qa_pairs(
            query=query if query else None,
            date_from=date_from,
            date_to=date_to,
            emotion_tone=emotion,
            conversation_id=conversation_id,
            page=1,
            per_page=10000  # Max results for export
        )

        if export_format == 'json':
            # Export as JSON
            output = json.dumps(results, ensure_ascii=False, indent=2)
            buffer = io.BytesIO(output.encode('utf-8'))
            buffer.seek(0)

            return send_file(
                buffer,
                mimetype='application/json',
                as_attachment=True,
                download_name=f'qa_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            )

        else:
            # Export as CSV
            output = io.StringIO()
            if results:
                fieldnames = ['id', 'question_pt', 'question_en', 'answer_pt', 'answer_en',
                             'context', 'date', 'emotion_tone', 'file_name']
                writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(results)

            buffer = io.BytesIO(output.getvalue().encode('utf-8'))
            buffer.seek(0)

            return send_file(
                buffer,
                mimetype='text/csv',
                as_attachment=True,
                download_name=f'qa_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            )

    except Exception as e:
        return jsonify({'error': 'Export failed', 'message': str(e)}), 500


# ============================================================================
# Statistics Endpoint
# ============================================================================

@app.route('/api/stats', methods=['GET'])
@token_required
def get_statistics(current_user):
    """Get database statistics"""
    try:
        stats = db.get_statistics()
        return jsonify(stats), 200

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve statistics', 'message': str(e)}), 500


# ============================================================================
# Investment Analysis Endpoints
# ============================================================================

@app.route('/api/investment-analysis', methods=['GET'])
@token_required
def get_investment_analysis(current_user):
    """Get all investment analysis data with optional filtering"""

    # Get query parameters for filtering
    query = request.args.get('q', '').strip().lower()
    method = request.args.get('method', '').strip().lower()  # direct, indirect
    interest_level = request.args.get('interest_level', '').strip().lower()  # low, medium, high
    min_effectiveness = request.args.get('min_effectiveness', type=int)
    max_effectiveness = request.args.get('max_effectiveness', type=int)
    transition_quality = request.args.get('transition_quality', '').strip().lower()  # natural, forced
    technique = request.args.get('technique', '').strip().lower()
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    try:
        # Get path to investment analysis directory
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'add_contact_phrase', 'investment_analysis'
        )

        if not os.path.exists(data_dir):
            return jsonify({'error': 'Investment analysis directory not found'}), 404

        # Load all JSON files
        all_instances = []
        file_list = glob.glob(os.path.join(data_dir, '*.json'))

        for file_path in file_list:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    # Add file metadata to each instance
                    for instance in data.get('investment_instances', []):
                        instance['metadata'] = data.get('metadata', {})
                        instance['file_name'] = os.path.basename(file_path)
                        all_instances.append(instance)

            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")
                continue

        # Apply filters
        filtered_instances = []
        for instance in all_instances:
            # Text search in exact_phrasing, techniques, and responses
            if query:
                searchable_text = ' '.join([
                    instance.get('analysis', {}).get('investment_introduction', {}).get('exact_phrasing', '').lower(),
                    ' '.join(instance.get('analysis', {}).get('investment_introduction', {}).get('key_techniques_used', [])).lower(),
                    instance.get('analysis', {}).get('reaction', {}).get('immediate_response', '').lower(),
                ]).lower()

                if query not in searchable_text:
                    continue

            # Method filter
            if method:
                instance_method = instance.get('analysis', {}).get('investment_introduction', {}).get('method', '').lower()
                if instance_method != method:
                    continue

            # Interest level filter
            if interest_level:
                instance_interest = instance.get('analysis', {}).get('reaction', {}).get('interest_level', '').lower()
                if instance_interest != interest_level:
                    continue

            # Effectiveness rating filter
            effectiveness = instance.get('analysis', {}).get('investment_introduction', {}).get('effectiveness_rating')
            if min_effectiveness is not None and effectiveness and effectiveness < min_effectiveness:
                continue
            if max_effectiveness is not None and effectiveness and effectiveness > max_effectiveness:
                continue

            # Transition quality filter
            if transition_quality:
                instance_transition = instance.get('analysis', {}).get('lead_up', {}).get('transition_quality', '').lower()
                if instance_transition != transition_quality:
                    continue

            # Technique filter
            if technique:
                techniques = [t.lower() for t in instance.get('analysis', {}).get('investment_introduction', {}).get('key_techniques_used', [])]
                if technique not in ' '.join(techniques):
                    continue

            filtered_instances.append(instance)

        # Sort by timestamp (newest first)
        filtered_instances.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        # Pagination
        total_count = len(filtered_instances)
        total_pages = (total_count + per_page - 1) // per_page
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        paginated_results = filtered_instances[start_idx:end_idx]

        return jsonify({
            'results': paginated_results,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total_results': total_count,
                'total_pages': total_pages
            },
            'filters': {
                'q': query,
                'method': method,
                'interest_level': interest_level,
                'min_effectiveness': min_effectiveness,
                'max_effectiveness': max_effectiveness,
                'transition_quality': transition_quality,
                'technique': technique
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve investment analysis', 'message': str(e)}), 500


@app.route('/api/investment-analysis/filters', methods=['GET'])
@token_required
def get_investment_filters(current_user):
    """Get available filter options for investment analysis"""
    try:
        # Get path to investment analysis directory
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'add_contact_phrase', 'investment_analysis'
        )

        if not os.path.exists(data_dir):
            return jsonify({'error': 'Investment analysis directory not found'}), 404

        # Collect unique values for filters
        methods = set()
        interest_levels = set()
        transition_qualities = set()
        techniques = set()
        effectiveness_ratings = []

        file_list = glob.glob(os.path.join(data_dir, '*.json'))

        for file_path in file_list:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    for instance in data.get('investment_instances', []):
                        analysis = instance.get('analysis', {})

                        # Collect methods
                        method = analysis.get('investment_introduction', {}).get('method')
                        if method:
                            methods.add(method)

                        # Collect interest levels
                        interest = analysis.get('reaction', {}).get('interest_level')
                        if interest:
                            interest_levels.add(interest)

                        # Collect transition qualities
                        transition = analysis.get('lead_up', {}).get('transition_quality')
                        if transition:
                            transition_qualities.add(transition)

                        # Collect techniques
                        techs = analysis.get('investment_introduction', {}).get('key_techniques_used', [])
                        techniques.update(techs)

                        # Collect effectiveness ratings
                        rating = analysis.get('investment_introduction', {}).get('effectiveness_rating')
                        if rating is not None:
                            effectiveness_ratings.append(rating)

            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")
                continue

        return jsonify({
            'methods': sorted(list(methods)),
            'interest_levels': sorted(list(interest_levels)),
            'transition_qualities': sorted(list(transition_qualities)),
            'techniques': sorted(list(techniques)),
            'effectiveness_range': {
                'min': min(effectiveness_ratings) if effectiveness_ratings else 0,
                'max': max(effectiveness_ratings) if effectiveness_ratings else 10
            }
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve filters', 'message': str(e)}), 500


@app.route('/api/investment-analysis/stats', methods=['GET'])
@token_required
def get_investment_stats(current_user):
    """Get statistics for investment analysis data"""
    try:
        # Get path to investment analysis directory
        data_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'data', 'add_contact_phrase', 'investment_analysis'
        )

        if not os.path.exists(data_dir):
            return jsonify({'error': 'Investment analysis directory not found'}), 404

        total_files = 0
        total_instances = 0
        effectiveness_ratings = []
        interest_level_counts = {'low': 0, 'medium': 0, 'high': 0}
        method_counts = {'direct': 0, 'indirect': 0}
        technique_counts = {}

        file_list = glob.glob(os.path.join(data_dir, '*.json'))
        total_files = len(file_list)

        for file_path in file_list:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    instances = data.get('investment_instances', [])
                    total_instances += len(instances)

                    for instance in instances:
                        analysis = instance.get('analysis', {})

                        # Effectiveness ratings
                        rating = analysis.get('investment_introduction', {}).get('effectiveness_rating')
                        if rating is not None:
                            effectiveness_ratings.append(rating)

                        # Interest levels
                        interest = analysis.get('reaction', {}).get('interest_level', '').lower()
                        if interest in interest_level_counts:
                            interest_level_counts[interest] += 1

                        # Methods
                        method = analysis.get('investment_introduction', {}).get('method', '').lower()
                        if method in method_counts:
                            method_counts[method] += 1

                        # Techniques
                        techniques = analysis.get('investment_introduction', {}).get('key_techniques_used', [])
                        for tech in techniques:
                            technique_counts[tech] = technique_counts.get(tech, 0) + 1

            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")
                continue

        # Calculate average effectiveness
        avg_effectiveness = sum(effectiveness_ratings) / len(effectiveness_ratings) if effectiveness_ratings else 0

        # Get top 10 techniques
        top_techniques = sorted(technique_counts.items(), key=lambda x: x[1], reverse=True)[:10]

        return jsonify({
            'total_files': total_files,
            'total_instances': total_instances,
            'average_effectiveness': round(avg_effectiveness, 2),
            'interest_level_distribution': interest_level_counts,
            'method_distribution': method_counts,
            'top_techniques': [{'technique': t[0], 'count': t[1]} for t in top_techniques]
        }), 200

    except Exception as e:
        return jsonify({'error': 'Failed to retrieve statistics', 'message': str(e)}), 500


# ============================================================================
# Health Check
# ============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    }), 200


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    print("=" * 60)
    print("QA Search Backend")
    print("=" * 60)
    print(f"Database: {config.DATABASE_PATH}")
    print(f"Host: {config.HOST}")
    print(f"Port: {config.PORT}")
    print(f"Debug: {config.DEBUG}")
    print("=" * 60)

    app.run(
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG
    )
