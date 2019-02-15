from flask import Flask, request, jsonify, render_template
from quiz import dbf
# import pymysql 已经导入pymysqlpool就不用了
import pymysqlpool
# pymysqlpool.logger.setLevel('DEBUG')
import configparser
# 读配置文件
config = configparser.ConfigParser()
config.read('db.ini')

conn_config = {
	'host':config['mysql']['host'],
	'port': int(config['mysql']['port']),
	'user':config['mysql']['usr'], 
	'password':config['mysql']['pwd'], 
	'database':config['mysql']['database'], 
	'autocommit':True
}

try: 
	# 初始化连接池
	quizPool = pymysqlpool.ConnectionPool(size=int(config['mysql']['pool_size']), name='quizPool', **conn_config) #初始化一个mysql连接池
	conn = quizPool.get_connection() # 获取一个连接
	cursor = conn.cursor() # 获取游标
	cursor.execute('select VERSION()') # 执行sql语句mysql版本
	quizPool.put_connection(conn) # 放回mysql连接，千万不能少
	print('mysql version：', cursor.fetchone()[0]) # 结果
	print('connPool size:', quizPool.size()) # 连接池大小
except Exception as e:
	# 初始化失败
	print(e)
	print('数据库连接池初始化失败')
	exit()
app = Flask(__name__)
#-----跨域----#

from flask_cors import CORS
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

quiz = dbf.quizMachine(quizPool) #初始化一个quiz类，封装了各种函数
@app.errorhandler(404)
def _error404(error):
	return '<h1>oops! 404 NOT FOUND.<br />This page does not exist.</h1>', 404
@app.route('/msg.php')
def _msg():
	return 'APP接口变更，请入群下载最新版本！'
@app.route('/api/msg')
def _apiMsg():
	return '祝大家都能上天~'
@app.route('/v1/')
def _v1():
	return render_template('old.html')
@app.route('/')
def _index():
	return render_template('index.html')
@app.route('/api/randQuestion')
def _randQuestion():
	data = {
		'status': 200,
		'data': [],
		'msg': ''
	}
	try:
		count = request.args.get('count')
		cg = request.args.get('cg')
		isfav = request.args.get('isfav')
		usr = request.args.get('usr')
		token = request.args.get('token')
		result = []
		msg = ''
		if int(count) > 200:
			count = '200'
		if quiz.verify(usr, token):
			if isfav == '1': # 只抽收藏
				result = quiz.randQuestionFav(count, cg, usr, False)
				msg = '从收藏抽题'
			elif isfav == '2': # 屏蔽模式
				result = quiz.randQuestionFav(count, cg, usr, True)
				msg = '屏蔽模式'
			else: # 全部抽
				result = quiz.randQuestionCG(count, cg)
				msg = '已登录全抽'
		else:
			result = quiz.randQuestionCG(count, cg)
			msg = '未登录全抽'
		data['data'] = result
		data['msg'] = msg
	except Exception as e:
		print(e)
		data['msg'] = '抽题失败except'
		data['status'] = 406
	return jsonify(data)
@app.route('/api/favrank')
def _rank():
	
	data = {
		'status': 200,
		'data': []
	}
	try:
		result = quiz.favrank()
		data['data'] = result
	except:
		data['status'] = 404
	return jsonify(data)
@app.route('/api/user/reg')
def _check():
	data = {
		'status': 200,
		'data': {
			'msg': 'server error.'
		}
	}
	try:
		usr = request.args.get('usr')
		pwd = request.args.get('pwd')
		print(usr, pwd)
		if len(usr)>=6 and len(pwd)>=6:
			# 这里插入用户信息
			result = quiz.reg(usr, pwd)
			if result:
				data['data']['msg'] = 'succeeded'
				pass
			else:
				data['data']['msg'] = 'registered'
				data['status'] = 403 #插入失败，已经注册
		else:
			data['data']['msg'] = '账号和密码长度必须大于等于6位'
			data['status'] = 404 #长度问题
	except:
		print('抛出异常')
		data['status'] = 406
	return jsonify(data)
@app.route('/api/user/verify')
def _verify():
	data = {
		'status': 200,
		'data': []
	}
	try:
		usr = request.args.get('usr')
		token = request.args.get('token')
		print(usr, token)
		if quiz.verify(usr, token):
			return jsonify(data)
		else:
			data['status'] = 404
			return jsonify(data)
	except Exception as e:
		print(e)
		data['status'] = 406
		return jsonify(data)
@app.route('/api/user/login')
def _login():
	data = {
		'status': 200,
		'data': []
	}
	try:
		usr = request.args.get('usr')
		pwd = request.args.get('pwd')
		result = quiz.login(usr, pwd)
		if result:
			data['data'] = result
		else:
			data['status'] = 404
	except:
		data['status'] = 406
	return jsonify(data)
@app.route('/api/user/addfav')
def _addfav():
	data = {
		'status': 200,
		'data': []
	}
	try:
		usr = request.args.get('usr')
		token = request.args.get('token')
		_id = request.args.get('id')
		if quiz.addfav(_id, usr, token):
			pass # 好像什么都不用做……
		else:
			data['status'] = 404
			pass
	except:
		data['status'] = 406
	return jsonify(data)
@app.route('/api/user/addblock')
def _addblock():
	data = {
		'status': 200,
		'data': []
	}
	try:
		usr = request.args.get('usr')
		token = request.args.get('token')
		_id = request.args.get('id')
		if quiz.addblock(_id, usr, token):
			pass # 好像什么都不用做……
		else:
			data['status'] = 404
			pass
	except:
		data['status'] = 406
	return jsonify(data)
	
@app.route('/api/user/listfav')
def _listfav():
	data = {
		'status': 200,
		'data': []
	}
	usr =request.args.get('usr')
	token = request.args.get('token')
	cg = request.args.get('cg')
	page = request.args.get('page')
	if not cg:
		cg = 0
	result = quiz.listfav(usr, token, int(page), cg)
	data['data'] = result
	return jsonify(data)
@app.route('/api/search')
def _search():
	data = {
		'status': 200,
		'data': []
	}
	keyword = request.args.get('keyword')
	result = quiz.search(keyword)
	try:
		if result:
			data['data'] = result
		else:
			data['status'] = 404
	except:
		data['status'] = 404
	return jsonify(data)
@app.route('/api/getnotes')
def _getNotes():
	_id = request.args.get('id')
	usr = request.args.get('usr')
	if not usr:
		usr = '#'
	return jsonify(quiz.getNotes(_id, usr))
@app.route('/api/addnote')
def _addNote():
	_id = request.args.get('id')
	usr = request.args.get('usr')
	token = request.args.get('token')
	note = request.args.get('note')
	result = quiz.addNote(_id, usr, token, note)
	return jsonify(result)
@app.route('/api/user/setProfile')
def _serProfile():
	_id = request.args.get('id')
	usr = request.args.get('username')
	token = request.args.get('token')
	slogan = request.args.get('slogan')
	qq = request.args.get('qq')
	print(_id, usr, token, slogan, qq)
	result = quiz.setProfile(_id, usr, token, slogan, qq)
	return jsonify(result)
@app.route('/api/user/rmfav')
def _rmfav():
	_id = request.args.get('id')
	usr = request.args.get('usr')
	token = request.args.get('token')
	if not (_id and usr and token):
		return jsonify({
			'status': 406,
			'data': {
				'msg': '请勿乱入'
			}
			})
	print(_id, usr, token)
	return jsonify(quiz.rmFav(_id, usr, token))
@app.route('/api/user/getFavRatio')
def _getFavRatio():
	usr = request.args.get('usr')
	token = request.args.get('token')
	if usr and token:
		return jsonify(quiz.getFavRatio(usr, token))
	else:
		return 'args error.'
@app.route('/api/aboutAutherEye')
def _aboutAutherEye():
	return '9998'
@app.route('/api/getSchool')
def _getSchool():
	keyword = request.args.get('keyword')
	level = request.args.get('level')
	result = quiz.getSchool(keyword, level)
	return jsonify(result)
@app.route('/api/getCategories')
def _getCategories():
	return jsonify(
			['全部随机(default)',
            '万维随机',
            '乐学随机',
            '信息理论',
            '进制转换',
            '信息安全',
            '计算机系统',
            '计算机硬件',
            '程序设计',
            '计算机网络',
            '多媒体',
            'AI、IoT、云计算、大数据']
            )
if __name__ == '__main__':
	app.run(host = '0.0.0.0', port = 80, debug = True)

