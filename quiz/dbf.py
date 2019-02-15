class quizMachine:
	# cursor = []
	quizPool = []
	suc = 'succeeded.'
	fail = 'server error.'
	exc = 'exception occured.'
	conn = []
	def __init__(self, quizPool):
		# self.cursor = db.cursor()
		# self.conn = quizPool.get_connection(timeout=0, retry_num=0)
		self.quizPool = quizPool
	def pExecute(self, sql):
		conn = self.quizPool.get_connection(timeout=0, retry_num=0)
		print('当前空闲连接池：', self.quizPool.size())
		cursor = conn.cursor()
		try: # ↓sql异常会捕捉不到，搞了半天哟妈的，返回false
			if cursor.execute(sql):
				try:
					data = self.toDict(cursor)
					# data = cursor.fetchall()
				except:
					data = True
			else: # 出现异常是假
				data = False
			conn.close() # 正常就put回去
		except:
			conn.close() # 不正常就关闭，会自动创建新的，异常状态时put不可用
			data = False
		return data
	def toDict(self, cursor):
		questions = cursor.fetchall()
		col = cursor.description
		result = []
		title = []
		for c in col:
			title.append(c[0])
		for question in questions:
			result.append(dict(list(zip(title, question))))
		return result
	def safeString(self, s):
		return s.replace('"', '\\"').replace("'", "\\'")
	def verify(self, usr, token):
		print('verify-> ', usr, token)
		usr = self.safeString(usr)
		token = self.safeString(token)
		sql = "call cktoken('{}', '{}')".format(usr, token)
		result = self.pExecute(sql)
		return result
	def randQuestionFav(self, count, cgID, usr, block):
		usr = self.safeString(usr)
		print('randQuestion-> ', usr)
		if block: # 屏蔽考试题目
			result = self.pExecute('call randQuestionBlock({}, {}, "{}")'.format(count, cgID, usr))
		else: # 只从考试抽题
			result = self.pExecute("call randQuestionFav({}, {}, '{}')".format(count, cgID, usr))
		return result
	def randQuestionCG(self, count, cg):
		print('randAll-> ', count)
		result = self.pExecute('call randQuestionCG({}, {})'.format(count, cg))
		return result
	def favrank(self):
		self.cursor.execute('call favrank()')
		# result = self.toDict()
		return result
	def login(self, usr, pwd):
		usr = self.safeString(usr)
		pwd = self.safeString(pwd)
		print('login-> ', usr, pwd)
		result = self.pExecute('SELECT *, unix_timestamp(time) as time FROM users WHERE username="{}" AND password="{}"'.format(usr, pwd))
		return result[0]
	def reg(self, usr, pwd):
		usr = self.safeString(usr)
		pwd = self.safeString(pwd)
		print('reg-> ', usr, pwd)
		sql = 'call reg("{}","{}")'.format(usr, pwd)
		# print(sql)
		try:
			result = self.pExecute(sql)
			return result
		except:
			return False
		return False
	def addblock(self, _id, usr, token):
		usr = self.safeString(usr)
		token = self.safeString(token)
		# self.db.ping(reconnect=True)
		print('addblock-> ', usr)
		result = False
		if self.verify(usr, token):
			result = self.pExecute('INSERT INTO blocks VALUES({},"{}", now())'.format(_id, usr))
		return result
	def addfav(self,  _id, usr, token):
		usr = self.safeString(usr)
		token = self.safeString(token)
		print('addfav-> ', usr)
		sql = 'INSERT INTO favs VALUES({},"{}", now())'.format(_id, usr)
		if self.verify(usr, token):
			try:
				result = self.pExecute(sql)
				 # result
			except:
				result = False
				pass
		return result

		# note = self.safeString(note)
		# # self.db.ping(reconnect=True)
		# data = {
		# 	'status': 200,
		# 	'msg': 'suc'
		# }
		# print('addNote-> ', usr)
		# if self.verify(usr, token): # token正确
		# 	try:
		# 		result = self.pExecute('call addnote({}, "{}","{}")'.format(_id, usr, note))
		# 		if result: # sql执行成功
		# 			pass
		# 		else: # sql不成功
		# 			data['status'] = 403
		# 			data['msg'] = 'can not execute.'
		# 	except: # 
		# 		data['status'] = 406
		# 		data['msg'] = 'exception occured.'
		# else: # token错误
		# 	data['status'] = 404
		# return data
	def listfav(self, usr, token, page, cg):
		# self.db.ping(reconnect=True)
		usr = self.safeString(usr)
		token = self.safeString(token)
		print('lsitfav-> ', usr)
		count = 15
		data = {
			'row_count': 0,
			'result': []
		}
		if self.verify(usr, token):
			try:
				row_count = len(self.pExecute('SELECT * FROM favs WHERE username = "{}"'.format(usr)))
				data['row_count'] = row_count
				data['result'] = self.pExecute('call listfav({}, "{}", {}, {})'.format(cg, usr, (page-1)*count, count))
			except:
				pass
		return data
	def search(self, keyword):
		keyword = keyword.replace('"', '\\"')
		print('search-> ', keyword)
		# self.db.ping(reconnect=True)
		data = {
			'row_count': 0,
			'result': []
		}
		sql = 'SELECT * FROM questions WHERE\
			title like "%{0}%"\
			or A like "%{0}%"\
			or B like "%{0}%"\
			or C like "%{0}%"\
			or D like "%{0}%"'.format(keyword)
		result = self.pExecute(sql)
		if result:
			row_count = len(result)
			data['result'] = result[:70]
		else:
			row_count = 0
		data['row_count'] = row_count
		
		return data
	def addNote(self, _id, usr, token, note): # 一定要有usr
		note = self.safeString(note)
		# self.db.ping(reconnect=True)
		data = {
			'status': 200,
			'msg': 'suc'
		}
		print('addNote-> ', usr)
		if self.verify(usr, token): # token正确
			try:
				result = self.pExecute('call addnote({}, "{}","{}")'.format(_id, usr, note))
				if result: # sql执行成功
					pass
				else: # sql不成功
					data['status'] = 403
					data['msg'] = 'can not execute.'
			except: # 
				data['status'] = 406
				data['msg'] = 'exception occured.'
		else: # token错误
			data['status'] = 404
		return data
	def getNotes(self, _id, usr): # 如果usr是#号，那么就取出所有评论
		# self.db.ping(reconnect=True)
		usr = self.safeString(usr)
		

		data = {
			'status': 200,
			'data': {
				'notes': [],
				'msg': self.suc
			}
		}
		# try:
		print('getNotes-> ', usr)
		sql = 'call getNotes({},"{}")'.format(_id, usr)
		result = self.pExecute(sql)
		print('getNOtes-> ', usr)
		data['data']['notes'] = result
		return data
	# except Exception as e:
		# print(e)
		data['data']['msg'] = self.exc
		data['status'] = 406
		return data
	def setProfile(self, _id, usr, token, slogan, qq):
		# self.db.ping(reconnect=True)
		usr = self.safeString(usr)
		token = self.safeString(token)
		slogan = self.safeString(slogan)
		qq = self.safeString(qq)
		print('serProfile-> ', usr)
		data = {
			'status': 200,
			'data': {
				'msg': self.suc
			}
		}
		if self.verify(usr, token):
			sql = 'UPDATE users SET slogan="{}", qq="{}" WHERE id={}'.format(slogan, qq, _id)
			result = self.pExecute(sql)
			if result:
				pass
			else:
				data['status'] = 403
				data['data']['msg'] = self.exc
		else:
			data['status'] = 404
			data['data']['msg'] = self.fail
		return data
	def rmFav(self, _id, usr, token):

		# self.db.ping(reconnect=True)
		usr = self.safeString(usr)
		token = self.safeString(token)
		print('rmFav-> ', usr)
		data = {
			'status': 200,
			'data': {
				'msg': self.suc
			}
		}
		if self.verify(usr, token):
			sql = 'DELETE FROM favs WHERE username ="{}" AND id={}'.format(usr, _id)
			result = self.pExecute(sql)
			if result:
				pass
			else:
				data['status'] = 403
				data['data']['msg'] =self.exc
		else:
			data['status'] = 404
			data['data']['msg'] = self.fail
		return data
	def getFavRatio(self, usr, token):
		data = {
			'status': 200,
			'data': []
		}
		usr = self.safeString(usr)
		token = self.safeString(token)
		print('getFavRatio-> ', usr)
		if self.verify(usr, token):
			sql = 'call getFavRatio("{}")'.format(usr)
			result = self.pExecute(sql)
			data['data'] = result
		else:
			data['status'] = 404
		return data
	def getSchool(self, keyword, level):
		keyword = self.safeString(keyword)
		data = {
			'status': 200,
			'data': []
		}
		print('getSchool-> ', keyword)
		if level != '0':
			sql = ('SELECT * FROM schools WHERE name LIKE "%{}%" AND level={}'.format(keyword, level))
		else:
			sql = ('SELECT * FROM schools WHERE name LIKE "%{}%"'.format(keyword))
		result = self.pExecute(sql)
		data ['data'] = result
		return data
if __name__ == '__main__':
	import pymysql
	db = pymysql.connect("localhost","root","root","quiz")
	s = quizMachine(db)
	print(s.randQuestionFav(10,  200, 'admin'))

