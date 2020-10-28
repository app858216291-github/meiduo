var vm = new Vue({
    el: '.header_con',
    data: {
        username: '',
    },
    mounted(){
        // 从 cookie 中获取保存的 username 用户
        // this.username = Cookies.get('username');
    }
});
