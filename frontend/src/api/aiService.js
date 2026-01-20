import request from '../utils/request';

export function chatWithAI(data) {
    return request({
        url: '/api/chat',
        method: 'post',
        data
    });
}

export function generateFormula(data) {
    return request({
        url: '/api/generate_formula',
        method: 'post',
        data
    });
}