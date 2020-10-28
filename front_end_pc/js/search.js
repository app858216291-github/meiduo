var vm = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'], // 修改vue模板符号，防止与django冲突
    data: {
        host: host,
        username: sessionStorage.username || localStorage.username,
        user_id: sessionStorage.user_id || localStorage.user_id,
        token: sessionStorage.token || localStorage.token,
        page: 1, // 当前页数
        page_size: 6, // 每页数量
        count: 0,  // 总数量
        skus: [], // 数据
        query: '',  // 查询关键字
        cart_total_count: 0, // 购物车总数量
        cart: [], // 购物车数据
    },
    computed: {
        total_page: function(){  // 总页数
            return Math.ceil(this.count/this.page_size);
        },
        next: function(){  // 下一页
            if (this.page >= this.total_page) {
                return 0;
            } else {
                return this.page + 1;
            }
        },
        previous: function(){  // 上一页
            if (this.page <= 0 ) {
                return 0;
            } else {
                return this.page - 1;
            }
        },
        page_nums: function(){  // 页码
            // 分页页数显示计算
            // 1.如果总页数<=5
            // 2.如果当前页是前3页
            // 3.如果当前页是后3页,
            // 4.既不是前3页，也不是后3页
            var nums = [];
            if (this.total_page <= 5) {
                for (var i=1; i<=this.total_page; i++){
                    nums.push(i);
                }
            } else if (this.page <= 3) {
                nums = [1, 2, 3, 4, 5];
            } else if (this.total_page - this.page <= 2) {
                for (var i=this.total_page; i>this.total_page-5; i--) {
                    nums.push(i);
                }
            } else {
                for (var i=this.page-2; i<this.page+3; i++){
                    nums.push(i);
                }
            }
            return nums;
        }
    },
    mounted: function(){
        // 向API服务请求获取csrftoken的值并存入cookie
        this.get_csrf_token();
        this.query = this.get_query_string('q');
        this.get_search_result();
        this.get_cart();
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
        // 获取url路径参数
        get_query_string: function(name){
            var reg = new RegExp('(^|&)' + name + '=([^&]*)(&|$)', 'i');
            var r = window.location.search.substr(1).match(reg);
            if (r != null) {
                return decodeURI(r[2]);
            }
            return null;
        },
        // 请求查询结果
        get_search_result: function(){
            // var url = this.host+'/skus/search/'
            var url = this.host+'/search/'
            axios.get(url, {
                params: {
                    q: this.query,
                    page: this.page,
                    page_size: this.page_size,
                },
                responseType: 'json',
                withCredentials:true,
            })
            .then(response => {
                this.skus = response.data.skus;
                this.count = response.data.count;
                this.page_size = response.data.page_size;
                this.query = response.data.query;

                for(var i=0; i< this.skus.length; i++){
                    this.skus[i].url = '/goods/' + this.skus[i].id + ".html";
                }
            })
            .catch(error => {
                console.log(error);
            })
        },
        // 点击页数
        on_page: function(num){
            if (num != this.page && num <= this.page_size){
                this.page = num;
                this.get_search_result();
            }
        },
        // 获取购物车数据
        get_cart: function(){

        }
    }
});
