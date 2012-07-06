from flask import Flask, render_template, session, request,\
        redirect, url_for, make_response

from ims_lti_py import ToolConsumer, ToolConfig,\
        OutcomeRequest, OutcomeResponse

import hashlib

app = Flask(__name__)
app.secret_key = '\xb9\xf8\x82\xa9\xf4\xdcC\xf4L<\x9c\xf1\x87\xa6\x7fI\xb9\x04\x9d\xed\xb0\xf2\x83\x0c'

@app.route('/', methods = ['GET'])
def index():
    return render_template('index.html')

@app.route('/set_name', methods = ['POST'])
def set_name():
    session['username'] = request.form['username']
    return redirect(url_for('tool_config'))

@app.route('/tool_config', methods = ['GET'])
def tool_config():
    if not session.get('username'):
        return redirect(url_for('index'))

    return render_template('tool_config.html',
            message = request.form.get('message'),
            username = session['username'])

@app.route('/tool_launch', methods = ['POST'])
def tool_launch():
    # Parse form and ensure necessary parameters are included
    for param in ['tool_name', 'launch_url', 'consumer_key',
            'consumer_secret']:
        if request.form.get(param) == None:
            return redirect(url_for('tool_config?message=Please%20set%20all%values'))

    # Create a new tool configuration
    config = ToolConfig(title = request.form.get('tool_name'),
            launch_url = request.form.get('launch_url'))
    config.set_custom_param('message_from_flask', 'hey from the flask example consumer') 

    # Create tool consumer! Yay LTI!
    consumer = ToolConsumer(request.form.get('consumer_key'),
            request.form.get('consumer_secret'))
    consumer.set_config(config)

    # Set some launch data from: http://www.imsglobal.org/LTI/v1p1pd/ltiIMGv1p1pd.html#_Toc309649684
    # Only this first one is required, but the rest are recommended
    consumer.resource_link_id = 'thisistotallyunique'
    consumer.launch_presentation_return_url = request.url + '/tool_return'
    consumer.lis_person_name_given = session['username']
    hash = hashlib.md5()
    hash.update(session['username'])
    consumer.user_id = hash.hexdigest()
    consumer.roles = 'learner'
    consumer.context_id = 'bestcourseever'
    consumer.context_title = 'Example Flask Tool Consumer'
    consumer.tool_consumer_instance_name = 'Frankie'

    if request.form.get('assignment'):
        consumer.lis_outcome_service_url = request.scheme + '://' +\
                request.host + '/grade_passback'
        consumer.list_result_sourcedid = 'oi'

    autolaunch = True if request.form.get('autolaunch') else False

    return render_template('tool_launch.html',
            autolaunch = autolaunch,
            launch_data = consumer.generate_launch_data(),
            launch_url = consumer.launch_url)

@app.route('/tool_return', methods = ['GET'])
def tool_return():
    error_message = request.args.get('lti_errormsg')
    message = request.args.get('lti_msg')
    return render_template('tool_return',
            message =  message,
            error_message = error_message)

@app.route('/grade_passback', methods = ['POST'])
def grade_passback():
    import ipdb; ipdb.set_trace()
    outcome_request = OutcomeRequest.from_post_request(request)
    sourcedid = outcome_request.lis_result_sourcedid
    consumer = ToolConsumer('test', 'secret')
    if consumer.is_valid_request(request):
        # TODO: Check oauth timestamp
        # TODO: Check oauth nonce
        
        response = OutcomeResponse()
        response.message_ref_identifier = outcome_request.message_identifier
        response.operation = outcome_request.operation
        response.code_major = 'success'
        response.severity = 'status'

        if outcome_request.is_replace_request():
            response.description = 'Your old score of 0 has been replaced with %s' %(outcome_request.score)
        elif outcome_request.is_delete_request():
            response.description = 'Your score is 50'
            response.score = 50
        elif outcome_request.is_delete_request():
            response.description = 'Your score has been cleared'
        else:
            response.code_major = 'unsupported'
            response.severity = 'status'
            response.description = '%s is not supported' %(outcome_request.operation)

        #headers = { 'Content-Type': 'text/xml' }
        return response.generate_response_xml()
    else:
        throw_oauth_error()

def throw_oauth_error():
    resp = make_response('Not authorized', 401)
    resp.headers['WWW-Authenticate'] = 'OAuth realm="%s"' %(request.host)
    return resp

if __name__ == '__main__':
    app.run(port = 5001)
