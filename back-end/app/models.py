from app import db
from werkzeug.security import generate_password_hash, check_password_hash
from flask import url_for


# API中需要返回一个所有用户的集合，
# 所以需要一个添加一个collect_dict的方法，考虑到后续会创建post等模型，所以用一个通用类


class PagniatedAPIMixin(object):
    @staticmethod
    def to_collection_dict(query, page, per_page, endpoint, **kwargs):
        resources = query.paginate(page, per_page, False)
        data = {
            'items': [item.to_dict() for item in resources.items],
            '_meta': {
                'page': page,
                'per_page': per_page,
                'total_pages': resources.pages,
                'total_items': resources.total
            },
        'links': {
            'self': url_for(endpoint, page=page, per_page=per_page,
                            **kwargs),
            'next': url_for(endpoint, page=page + 1, per_page=per_page,
                            **kwargs) if resources.has_next else None,
            'prev': url_for(endpoint, page=page - 1, per_page=per_page,
                            **kwargs) if resources.has_prev else None
        }
        }
        return data


class User(PagniatedAPIMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    # 不会去保存原始密码

    def __repr__(self):
        return '<User {}>'.format(self.username)

    def set_password(self,password):
        self.password_hash = generate_password_hash(password)

    def check_password(self,password):
        return check_password_hash(self.password_hash,password)

    # 后端生成的User实例对象，而返回给前端时，需要传递一个JSON对象。该方法首先是返回一个字典再用flask.jsonify转换成json
    def to_dict(self,include_email = False):
        data = {
            'id': self.id,
            'username': self.username,
            'links' :{
                'self': url_for('api.get_user', id = self.id)
            # 这里的get_user用的就是user.py里面的get_user函数
            }
        }
        # 说明：只有当用户请求自己的数据时才包含email，使用include_email标签来判断该字段是否在字典中
        if include_email:
            data['email'] = self.email
        return data


    # 利用前端发送的JSON对象，转换成User对象
    def from_dict(self, data, new_user=False):
        for field in ['username','email']:
            if field in data:
                setattr(self,field,data[field])
            if new_user and 'password' in data:
                self.set_password(data['password'])