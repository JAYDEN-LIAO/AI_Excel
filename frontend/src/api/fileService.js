import request from '../utils/request';

export function uploadFile(formData) {
    return request({
        url: '/api/upload',
        method: 'post',
        data: formData,
        headers: { 'Content-Type': 'multipart/form-data' }
    });
}

export function getFileData(fileId) {
    return request({
        url: `/api/files/${fileId}/data`,
        method: 'get'
    });
}

// 🟢 新增：获取历史对照列表
export function getHistoryList(params) {
    return request({
        url: '/api/history',
        method: 'get',
        params // 可以传 { q: '文件名' }
    });
}