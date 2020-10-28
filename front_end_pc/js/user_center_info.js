var vm = new Vue({
    el: '#app',
    data: {
        host,
        username: '',
        mobile: '',
        email: '',
        email_active: false,
        set_email: false,
        send_email_btn_disabled: false,
        send_email_tip: '重新发送验证邮件',
        email_error: false,
        histories: [],
    },
    mounted: function () {
        // 向API服务请求获取csrftoken的值并存入cookie
        this.get_csrf_token();

        // 获取cookie中的用户名
        this.username = Cookies.get('username');

        // 获取个人信息:
        this.get_person_info()

        this.get_history()
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
                console.log(error);
            })
        },
        get_history:function(){
             // 添加下列代码, 发送请求, 获取用户的浏览记录信息:
            axios.get(this.host + '/browse_histories/', {
                responseType: 'json',
                withCredentials:true,
            })
            .then(response => {
                this.histories = response.data.skus;
                for(var i=0; i<this.histories.length; i++){
                  this.histories[i].url='/goods/'+this.histories[i].id + '.html';
                }
            })
            .catch(error => {
                console.log(error)
            });
        },
        // 获取用户所有的资料
        get_person_info: function () {
            var url = this.host + '/user/';
            axios.get(url, {
                responseType: 'json',
                withCredentials: true
            })
            .then(response => {
                if (response.data.code == 400) {
                    // 打印错误提示信息
                    alert(response.data.message);
                    location.href = 'login.html'
                    return
                }
                this.username = response.data.user.username;
                this.mobile = response.data.user.mobile;
                this.email = response.data.user.email;
                this.email_active = response.data.user.email_active;
            })
            .catch(error => {
                this.set_email = false
                location.href = 'login.html'
            })
        },
        // 保存email
        save_email: function () {
            var re = /^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$/;
            if (re.test(this.email)) {
                this.email_error = false;
            } else {
                this.email_error = true;
                return;
            }

            // 进行前端页面请求:
            var url = this.host + '/user/email/'
            axios.put(url,
                {
                    email: this.email
                },
                {
                    responseType: 'json',
                    withCredentials:true,
                    headers: {
                        'X-CSRFToken': Cookies.get('csrftoken')
                    }
                })
                // 成功请求的回调
                .then(response => {
                    if (response.data.code == 0) {
                        this.set_email = false;
                        this.send_email_btn_disabled = true;
                        this.send_email_tip = '已发送验证邮件'
                    } else {
                        alert(response.data.message);
                    }
                })
                // 失败请求的回调:
                .catch(error => {
                    alert('请求失败, 失败原因:', error);
                });
        }
    }
});
