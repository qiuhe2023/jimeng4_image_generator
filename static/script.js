document.addEventListener('DOMContentLoaded', () => {
    const generateForm = document.getElementById('generate-form');
    const clearBtn = document.getElementById('clear-btn');
    const statusMessage = document.getElementById('status-message');
    const statusTitle = document.getElementById('status-title');
    const statusText = document.getElementById('status-text');
    const progressBar = document.getElementById('progress-bar');
    const resultsContainer = document.getElementById('results-container');
    const loadHistoryBtn = document.getElementById('load-history-btn');
    const closeHistoryBtn = document.getElementById('close-history-btn');
    const historySection = document.querySelector('.history-section');
    const historyContainer = document.getElementById('history-container');
    const scaleSlider = document.getElementById('scale');
    const scaleValue = document.getElementById('scale-value');

    // 更新滑块值显示
    scaleSlider.addEventListener('input', () => {
        scaleValue.textContent = scaleSlider.value;
    });

    // 清空表单
    clearBtn.addEventListener('click', () => {
        generateForm.reset();
        scaleValue.textContent = '0.5';
    });

    // 表单提交处理
    generateForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        // 显示状态信息
        statusMessage.classList.remove('hidden', 'success', 'error');
        statusTitle.textContent = '处理中...';
        statusText.textContent = '正在生成图片，请稍候...';
        progressBar.style.width = '0%';
        
        // 禁用生成按钮
        const generateBtn = document.getElementById('generate-btn');
        generateBtn.disabled = true;
        generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 生成中...';
        
        // 隐藏结果容器中的空状态
        const emptyState = resultsContainer.querySelector('.empty-state');
        if (emptyState) {
            resultsContainer.removeChild(emptyState);
        }

        try {
            // 收集表单数据
            const formData = new FormData(generateForm);
            const data = Object.fromEntries(formData.entries());
            
            // 开始进度条动画
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress += 1;
                if (progress <= 90) { // 只到90%，留10%给最终完成
                    progressBar.style.width = `${progress}%`;
                }
            }, 100);

            // 调用API生成图片
            const response = await axios.post('/generate', data, {
                headers: {
                    'Content-Type': 'application/json'
                }
            });

            clearInterval(progressInterval);
            progressBar.style.width = '100%';
            
            if (response.data.status === 'success') {
                // 更新状态为成功
                statusTitle.textContent = '生成成功！';
                statusText.textContent = `已成功生成 ${response.data.files.length} 张图片`;
                statusMessage.classList.add('success');
                
                // 显示生成的图片
                displayResults(response.data.files);
                
                // 5秒后隐藏成功消息
                setTimeout(() => {
                    statusMessage.classList.add('hidden');
                }, 5000);
            } else {
                throw new Error(response.data.message || '生成失败');
            }
        } catch (error) {
            // 更新状态为错误
            statusTitle.textContent = '生成失败';
            statusText.textContent = error.response?.data?.message || error.message || '未知错误，请重试';
            statusMessage.classList.add('error');
        } finally {
            // 恢复生成按钮状态
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic"></i> 生成图片';
        }
    });

    // 显示生成结果
    function displayResults(files) {
        resultsContainer.innerHTML = '';
        
        files.forEach(filename => {
            const fileUrl = `/output/${filename}`;
            const resultCard = document.createElement('div');
            resultCard.className = 'result-card';
            
            resultCard.innerHTML = `
                <div class="result-image-container">
                    <img src="${fileUrl}" alt="生成的图片" class="result-image">
                </div>
                <div class="result-actions">
                    <a href="${fileUrl}" download="${filename}" class="btn btn-sm btn-primary">
                        <i class="fas fa-download"></i> 下载
                    </a>
                    <button class="btn btn-sm btn-secondary view-btn" data-url="${fileUrl}">
                        <i class="fas fa-eye"></i> 查看
                    </button>
                </div>
            `;
            
            resultsContainer.appendChild(resultCard);
        });
        
        // 添加查看按钮事件
        document.querySelectorAll('.view-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const url = btn.getAttribute('data-url');
                window.open(url, '_blank');
            });
        });
    }

    // 加载历史记录
    async function loadHistory() {
        try {
            const response = await axios.get('/output');
            
            if (response.data && response.data.files && response.data.files.length > 0) {
                historyContainer.innerHTML = '';
                
                response.data.files.forEach(filename => {
                    const fileUrl = `/output/${filename}`;
                    const historyItem = document.createElement('div');
                    historyItem.className = 'history-item';
                    
                    // 从文件名中提取时间戳和其他信息
                    const parts = filename.split('_');
                    const timestamp = parts[1] || '';
                    const readableTime = timestamp ? new Date(parseInt(timestamp)).toLocaleString() : '未知时间';
                    
                    historyItem.innerHTML = `
                        <div class="history-thumbnail">
                            <img src="${fileUrl}" alt="历史图片" class="history-image">
                        </div>
                        <div class="history-info">
                            <p class="history-filename">${filename}</p>
                            <p class="history-time">${readableTime}</p>
                        </div>
                        <div class="history-actions">
                            <a href="${fileUrl}" download="${filename}" class="btn btn-sm btn-primary">
                                <i class="fas fa-download"></i>
                            </a>
                            <button class="btn btn-sm btn-secondary view-btn" data-url="${fileUrl}">
                                <i class="fas fa-eye"></i>
                            </button>
                        </div>
                    `;
                    
                    historyContainer.appendChild(historyItem);
                });
                
                // 添加查看按钮事件
                document.querySelectorAll('.history-item .view-btn').forEach(btn => {
                    btn.addEventListener('click', () => {
                        const url = btn.getAttribute('data-url');
                        window.open(url, '_blank');
                    });
                });
            } else {
                historyContainer.innerHTML = `
                    <div class="empty-state">
                        <i class="fas fa-clock"></i>
                        <p>暂无历史记录</p>
                    </div>
                `;
            }
        } catch (error) {
            historyContainer.innerHTML = `
                <div class="empty-state error">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>加载历史记录失败</p>
                </div>
            `;
        }
    }

    // 查看历史记录按钮
    loadHistoryBtn.addEventListener('click', () => {
        historySection.classList.remove('hidden');
        loadHistory();
    });

    // 关闭历史记录按钮
    closeHistoryBtn.addEventListener('click', () => {
        historySection.classList.add('hidden');
    });
});