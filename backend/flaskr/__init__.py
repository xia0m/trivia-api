import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)

    @app.route('/')
    def index():
        return 'success'

    '''
		@TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
		'''
    cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

    '''
		@TODO: Use the after_request decorator to set Access-Control-Allow
		'''
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers',
                             'Content-Type,Authorization,true')
        response.headers.add('Access-Control-Allow-Methods',
                             'GET,PATCH,PUT,POST,DELETE,OPTIONS')
        return response

    '''
		@TODO:
		Create an endpoint to handle GET requests
		for all available categories.
		'''
    @app.route('/api/categories')
    def retrieve_categories():
        all_categories = Category.query.all()

        if len(all_categories) == 0:
            abort(404)
        formated_categories = [category.format()
                               for category in all_categories]
        categories = convert_list_to_dict(formated_categories)

        return jsonify({'success': True, 'categories': categories})
    '''
		@TODO:
		Create an endpoint to handle GET requests for questions,
		including pagination (every 10 questions).
		This endpoint should return a list of questions,
		number of total questions, current category, categories.

		TEST: At this point, when you start the application
		you should see questions and categories generated,
		ten questions per page and pagination at the bottom of the screen for three pages.
		Clicking on the page numbers should update the questions.
		'''
    def paginate_questions(request, selection):
        page = request.args.get('page', 1, type=int)
        start = (page-1) * QUESTIONS_PER_PAGE
        end = start + QUESTIONS_PER_PAGE

        questions = [question.format() for question in selection]
        current_questions = questions[start:end]

        return current_questions

    def convert_list_to_dict(formated_categories):
        categories = {}
        for item in formated_categories:
            categories[item['id']] = item['type']
        return categories

    @app.route('/api/questions')
    def retrieve_books():
        selection = Question.query.order_by(Question.id).all()
        current_questions = paginate_questions(request, selection)
        all_categories = Category.query.all()
        formated_categories = [category.format()
                               for category in all_categories]

        if len(current_questions) == 0 or len(formated_categories) == 0:
            abort(404)
        categories = convert_list_to_dict(formated_categories)

        return jsonify({
            'success': True,
            'questions': current_questions,
            'total_questions': len(Question.query.all()),
            'categories': categories,
            'current_category': 'History'
        })

    '''
		@TODO:
		Create an endpoint to DELETE question using a question ID.

		TEST: When you click the trash icon next to a question, the question will be removed.
		This removal will persist in the database and when you refresh the page.
		'''
    @app.route('/api/questions/<question_id>', methods=['DELETE'])
    def delete_question(question_id):
        try:
            question = Question.query.filter(
                Question.id == question_id).one_or_none()
            if question is None:
                abort(404)

            question.delete()

            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)

            return jsonify({
                'success': True,
                'deleted': question_id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })
        except:
            abort(422)

    '''
		@TODO:
		Create an endpoint to POST a new question,
		which will require the question and answer text,
		category, and difficulty score.

		TEST: When you submit a question on the "Add" tab,
		the form will clear and the question will appear at the end of the last page
		of the questions list in the "List" tab.
		'''
    @app.route('/api/questions', methods=['POST'])
    def create_question():
        body = request.get_json()

        new_question = body.get('question', None)
        new_answer = body.get('answer', None)
        new_difficulty = body.get('difficulty', 1)
        new_category = body.get('category', 1)

        try:

            question = Question(question=new_question, answer=new_answer,
                                category=new_category, difficulty=new_difficulty)
            question.insert()
            selection = Question.query.order_by(Question.id).all()
            current_questions = paginate_questions(request, selection)
            return jsonify({
                'success': True,
                'created': question.id,
                'questions': current_questions,
                'total_questions': len(Question.query.all())
            })
        except:
            abort(422)

    '''
		@TODO:
		Create a POST endpoint to get questions based on a search term.
		It should return any questions for whom the search term
		is a substring of the question.

		TEST: Search by any phrase. The questions list will update to include
		only question that include that string within their question.
		Try using the word "title" to start.
		'''
    @app.route('/api/search', methods=['POST'])
    def search_questions():
        body = request.get_json()
        term = body.get('searchTerm', None)

        query_results = Question.query.filter(
            Question.question.like(f"%{term}%")).order_by(Question.id).all()
        questions = [question.format() for question in query_results]
        if len(questions) == 0:
            questions = None
        return jsonify({
            'success': True,
            'questions': questions,
            'total_questions': len(query_results),
            'current_category': 'History'
        })

    '''
		@TODO:
		Create a GET endpoint to get questions based on category.

		TEST: In the "List" tab / main screen, clicking on one of the
		categories in the left column will cause only questions of that
		category to be shown.
		'''
    @app.route('/api/categories/<category_id>/questions', methods=['GET'])
    def retrieve_books_by_category(category_id):
        selections = Question.query.filter_by(
            category=category_id).all()
        formated_questions = paginate_questions(request, selections)

        if len(selections) == 0:
            abort(404)

        current_category = Category.query.get(category_id)

        return jsonify({
            'success': True,
            'questions': formated_questions,
            'total_questions': len(selections),
            'current_category': current_category.type
        })

    '''
		@TODO:
		Create a POST endpoint to get questions to play the quiz.
		This endpoint should take category and previous question parameters
		and return a random questions within the given category,
		if provided, and that is not one of the previous questions.

		TEST: In the "Play" tab, after a user selects "All" or a category,
		one question at a time is displayed, the user is allowed to answer
		and shown whether they were correct or not.
		'''
    @app.route('/api/quizzes', methods=['POST'])
    def play_quiz():
        body = request.get_json()

        previous_questions = body.get('previous_questions', [])
        quiz_category = body.get('quiz_category', {})

        if int(quiz_category['id']) == 0:
            questions = Question.query.all()
        else:
            questions = Question.query.filter_by(
                category=quiz_category['id']).all()

        formated_questions = [question.format() for question in questions]
        if len(formated_questions) == 0:
            abort(404)

        avaliable_quesitons = [
            q for q in formated_questions if q not in previous_questions]
        selected_question = random.choice(avaliable_quesitons)

        return jsonify({
            'success': True,
            'question': selected_question
        })

    '''
		@TODO:
		Create error handlers for all expected errors
		including 404 and 422.
		'''

    @app.errorhandler(400)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 400,
            'message': 'Bad Request'
        }), 400

    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'Method Not Allowed'
        }), 405

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            'success': False,
            'error': 500,
            'message': 'Internal Server Error'
        }), 500

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            'success': False,
            'error': 422,
            'message': 'unprocessable'
        }), 422

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 404,
            'message': 'resource not found'
        }), 404

    return app
