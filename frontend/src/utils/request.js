import axios from 'axios';
import { message } from 'ant-design-vue';

// 创建 axios 实例
const service = axios.create({
    baseURL: 'http://127.0.0.1:8000', // 你的 FastAPI 地址
    timeout: 60000 // 请求超时时间
});

// 响应拦截器
service.interceptors.response.use(
    response => {
        const res = response.data;
        return res;
    },
    error => {
        console.error('err' + error);
        message.error(error.message || '请求失败');
        return Promise.reject(error);
    }
);

export default service;