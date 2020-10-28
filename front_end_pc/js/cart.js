var vm = new Vue({
    el: '#app',
    delimiters: ['[[', ']]'],
    data: {
        host,
        username: '',
        user_id: sessionStorage.user_id || localStorage.user_id,
        token: sessionStorage.token || localStorage.token,
        cart: [],
        total_selected_count: 0,
        origin_input: 0 // 用于记录手动输入前的值
    },
    computed: {
        total_count: function(){
            var total = 0;
            for(var i=0; i<this.cart.length; i++){
                total += parseInt(this.cart[i].count);
                this.cart[i].amount = ((this.cart[i].price) * (this.cart[i].count)).toFixed(2);
            }
            return total;
        },
        total_selected_amount: function(){
            var total = 0;
            this.total_selected_count = 0;
            for(var i=0; i<this.cart.length; i++){
                if(this.cart[i].selected) {
                    total += ((this.cart[i].price) * (this.cart[i].count));
                    this.total_selected_count += parseInt(this.cart[i].count);
                }
            }
            return total.toFixed(2);
        },
        selected_all: function(){
            var selected=true;
            for(var i=0; i<this.cart.length; i++){
                if(this.cart[i].selected==false){
                    selected=false;
                    break;
                }
            }
            return selected;
        }
    },
    mounted: function(){
        this.username = Cookies.get('username')

        // 向API服务请求获取csrftoken的值并存入cookie
        this.get_csrf_token();

        // 获取购物车数据
        axios.get(this.host+'/carts/', {
                responseType: 'json',
                withCredentials: true
            })
            .then(response => {
                this.cart = response.data.cart_skus;
                for(var i=0; i<this.cart.length; i++){
                    this.cart[i].amount = ((this.cart[i].price) * this.cart[i].count).toFixed(2);
                }
            })
            .catch(error => {
                console.log(error.response.data);
            })
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
        // 退出
        logout: function(){
            var url = this.host + '/logout/';
            axios.delete(url, {
                responseType: 'json',
                withCredentials:true,
                headers: {
                    'X-CSRFToken': Cookies.get('csrftoken')
                }
            })
                .then(response => {
                    location.href = '/login.html';
                })
                .catch(error => {
                    console.log(error.response);
                })
        },
        // 减少操作
        on_minus: function(index){
            if (this.cart[index].count > 1) {
                var count = this.cart[index].count - 1;
                this.update_count(index, count);
            }
        },
        on_add: function(index){
            var count = this.cart[index].count + 1;
            this.update_count(index, count);
        },
        // 删除购物车数据
        on_delete: function(index){
            axios.delete(this.host+'/carts/', {
                    data: {
                        sku_id: this.cart[index].id
                    },
                    responseType: 'json',
                    withCredentials: true,
                    headers: {
                        'X-CSRFToken': Cookies.get('csrftoken')
                    }
                })
                .then(response => {
                    if (response.data.code == 0) {
                        this.cart.splice(index, 1);
                    }
                })
                .catch(error => {
                    console.log(error);
                })
        },
        on_input: function(index){
            var val = parseInt(this.cart[index].count);
            if (isNaN(val) || val <= 0) {
                this.cart[index].count = this.origin_input;
            } else {
                // 更新购物车数据
                axios.put(this.host+'/carts/', {
                    sku_id: this.cart[index].id,
                    count: val,
                    selected: this.cart[index].selected
                }, {
                    responseType: 'json',
                    withCredentials: true,
                    headers: {
                        'X-CSRFToken': Cookies.get('csrftoken')
                    }
                })
                .then(response => {
                    this.cart[index].count = response.data.cart_sku.count;
                })
                .catch(error => {
                    console.log(error)
                })
            }
        },
        // 更新购物车数据
        update_count: function(index, count){
            axios.put(this.host+'/carts/', {
                    sku_id: this.cart[index].id,
                    count,
                    selected: this.cart[index].selected
                }, {
                    responseType: 'json',
                    withCredentials: true,
                    headers: {
                        'X-CSRFToken': Cookies.get('csrftoken')
                    }
                })
                .then(response => {
                    this.cart[index].count = response.data.cart_sku.count;
                })
                .catch(error => {
                    console.log(error)
                })
        },
        // 更新购物车数据
        update_selected: function(index) {
            axios.put(this.host+'/carts/', {
                    sku_id: this.cart[index].id,
                    count: this.cart[index].count,
                    selected: this.cart[index].selected
                }, {
                    responseType: 'json',
                    withCredentials: true,
                    headers: {
                        'X-CSRFToken': Cookies.get('csrftoken')
                    }
                })
                .then(response => {
                    this.cart[index].selected = response.data.cart_sku.selected;
                })
                .catch(error => {
                    console.log(error);
                })
        },
        // 购物车全选
        on_selected_all: function(){
            var selected = !this.selected_all;
            axios.put(this.host + '/carts/selection/', {
                    selected: selected
                }, {
                    responseType: 'json',
                    withCredentials: true,
                    headers: {
                        'X-CSRFToken': Cookies.get('csrftoken')
                    }
                })
                .then(response => {
                    for (var i=0; i<this.cart.length;i++){
                        this.cart[i].selected = selected;
                    }
                })
                .catch(error => {
                    console.log(error);
                })
        },
    }
});
