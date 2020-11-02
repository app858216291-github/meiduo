var vm = new Vue({
    el: '#app',
    data: {
        host: host,
        username: '',

        old_pwd: '',
        new_pwd: '',
        new_cpwd: '',

        error_opwd: false,
        error_pwd: false,
        error_cpwd: false,
    },
    mounted: function () {
        // 给 username 赋值
        this.username = Cookies.get('username');
        // 向API服务请求获取csrftoken的值并存入cookie
        this.get_csrf_token();
    },
    methods: {
        // 获取csrf_token的值
        get_csrf_token: function(){
            var url = this.host + "/csrf_token/";
            axios.get(url)
            .then(response => {
                // 将响应数据中的csrf_token的值存入 csrftoken cookie
                Cookies.set('csrftoken', response.data.csrf_token);
            }).catch(error => {
                console.log(error);
            })
        },
        // 退出登录按钮
        logoutfunc: function () {
            var url = this.host + '/logout/';
            axios.delete(url, {
                responseType: 'json',
                withCredentials:true,
                headers: {
                    'X-CSRFToken': Cookies.get('csrftoken')
                }
            })
            .then(response => {
                location.href = 'login.html';
            })
            .catch(error => {
                console.log(error.response);
            })
        },
        // 表单提交按钮: 更换密码
        change_password: function () {
            this.check_opwd();
            this.check_pwd();
            this.check_cpwd();

            if (this.error_opwd == true || this.error_pwd == true || this.error_cpwd == true) {
                // 不满足修改密码条件：禁用表单
                window.event.returnValue = false;
                return;
            }

            var url = this.host + '/password/';
            axios.put(url, {
                old_password:this.old_pwd,
                new_password:this.new_pwd,
                new_password2:this.new_cpwd
            }, {
                responseType: 'json',
                withCredentials: true,
                headers: {
                    'X-CSRFToken': Cookies.get('csrftoken')
                }
            })
            .then(response => {
                if (response.data.code == 0) {
                    alert('密码修改成功!');
                    location.href = 'login.html'
                } else {
                    alert(response.data.message);
                }
            })
            .catch(error => {
                console.log(error);
            })
        }
        ,
        // 检查当前密码是否正确
        check_opwd: function () {
            var re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.old_pwd)) {
                this.error_opwd = false;
            } else {
                this.error_opwd = true;
            }
        }
        ,
        check_pwd: function () {
            var re = /^[0-9A-Za-z]{8,20}$/;
            if (re.test(this.new_pwd)) {
                this.error_pwd = false;
            } else {
                this.error_pwd = true;
            }
        }
        ,
        // 确认密码点击事件
        check_cpwd: function () {
            if (this.new_pwd != this.new_cpwd) {
                this.error_cpwd = true;
            } else {
                this.error_cpwd = false;
            }
        }
    }
})
