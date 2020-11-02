var vm = new Vue({
    el: '#email_result',

    data: {
        host:host,
        success: true
    },
    mounted: function(){
        // 向API服务请求获取csrftoken的值并存入cookie
        this.get_csrf_token();
        this.verify_email();
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
        // 验证用户邮箱
        verify_email: function(){
            var url = this.host + "/csrf_token/";
            axios.get(url)
            .then(response => {
                // 将响应数据中的csrf_token的值存入 csrftoken cookie
                Cookies.set('csrftoken', response.data.csrf_token);

                axios.put(this.host+'/emails/verification/'+ window.location.search, {}, {
                    responseType: 'json',
                    withCredentials: true,
                    headers: {
                        'X-CSRFToken': Cookies.get('csrftoken')
                    }
                })
                .then(response => {
                    this.success = true;
                })
                .catch(error => {
                    this.success = false;
                });
            }).catch(error => {
                console.log(error);
            })
        },
    }
});
