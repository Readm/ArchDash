"""
客户端回调函数模块
包含所有在浏览器端执行的JavaScript回调函数
"""

from dash import html, Output, Input


def register_arrow_display_callback(app):
    """注册Pin悬停箭头显示系统回调"""
    app.clientside_callback(
        """
        function(connections_data, canvas_children) {
            try {
                var arrowContainer = document.getElementById('arrows-overlay-dynamic');
                    if (!arrowContainer) {
                        console.log('箭头容器未找到');
                        return;
                    }

                    // 清除现有箭头
                    arrowContainer.innerHTML = '';

                    if (!connections_data || connections_data.length === 0) {
                        console.log('无依赖关系数据');
                        return;
                    }

                    console.log('初始化pin悬停箭头系统，连接数:', connections_data.length);

                    // 存储连接数据到全局变量，供事件处理器使用
                    window.arrowConnectionsData = connections_data;
                    window.arrowContainer = arrowContainer;

                    // 移除之前的事件监听器（避免重复绑定）
                    var pinElements = document.querySelectorAll('[id^="pin-"]');
                    for (var i = 0; i < pinElements.length; i++) {
                        var pin = pinElements[i];
                        pin.removeEventListener('mouseenter', window.pinMouseEnter);
                        pin.removeEventListener('mouseleave', window.pinMouseLeave);
                    }

                    // 定义鼠标进入pin的处理函数
                    window.pinMouseEnter = function(event) {
                        var pinId = event.target.id;
                        console.log('鼠标进入pin:', pinId);

                        // 添加active类
                        event.target.classList.add('active');

                        // 清除现有箭头
                        window.arrowContainer.innerHTML = '';

                        // 找到与当前pin相关的所有连接
                        var relevantConnections = window.arrowConnectionsData.filter(function(conn) {
                            return conn.source_pin_id === pinId || conn.target_pin_id === pinId;
                        });

                        console.log('找到相关连接:', relevantConnections.length);

                        // 绘制相关的箭头
                        drawArrows(relevantConnections, pinId);
                    };

                    // 定义鼠标离开pin的处理函数
                    window.pinMouseLeave = function(event) {
                        var pinId = event.target.id;
                        console.log('鼠标离开pin:', pinId);

                        // 移除active类
                        event.target.classList.remove('active');

                        // 延迟清除箭头（给用户时间移动到箭头上）
                        setTimeout(function() {
                            // 检查是否还有active的pin
                            var activePins = document.querySelectorAll('.param-pin.active');
                            if (activePins.length === 0) {
                                window.arrowContainer.innerHTML = '';
                                console.log('清除所有箭头');
                            }
                        }, 200);
                    };

                    // 绘制箭头的函数 - 使用SVG路径
                    function drawArrows(connections, activePinId) {
                        var containerRect = window.arrowContainer.getBoundingClientRect();

                        for (var i = 0; i < connections.length; i++) {
                            var connection = connections[i];

                            var sourcePin = document.getElementById(connection.source_pin_id);
                            var targetPin = document.getElementById(connection.target_pin_id);

                            if (sourcePin && targetPin) {
                                var sourceRect = sourcePin.getBoundingClientRect();
                                var targetRect = targetPin.getBoundingClientRect();

                                // 计算源pin的右边中点作为起始点
                                var x1 = sourceRect.right - containerRect.left;
                                var y1 = sourceRect.top + sourceRect.height / 2 - containerRect.top;

                                // 计算目标pin的左边中点作为结束点
                                var x2 = targetRect.left - containerRect.left;
                                var y2 = targetRect.top + targetRect.height / 2 - containerRect.top;

                                var dx = x2 - x1;
                                var dy = y2 - y1;
                                var length = Math.sqrt(dx * dx + dy * dy);

                                if (length > 5) {
                                    // 确定箭头颜色和样式
                                    var isActiveConnection = (connection.source_pin_id === activePinId || connection.target_pin_id === activePinId);
                                    var arrowColor = isActiveConnection ? '#e74c3c' : '#007bff';
                                    var arrowOpacity = isActiveConnection ? '1' : '0.6';
                                    var strokeWidth = isActiveConnection ? '3' : '2';

                                    // 创建SVG元素
                                    var svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
                                    svg.style.position = 'absolute';
                                    svg.style.top = '0';
                                    svg.style.left = '0';
                                    svg.style.width = '100%';
                                    svg.style.height = '100%';
                                    svg.style.pointerEvents = 'none';
                                    svg.style.zIndex = isActiveConnection ? '1002' : '1000';
                                    svg.style.overflow = 'visible';

                                    // 创建定义区域（包含渐变、滤镜等）
                                    var defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');

                                    // 创建线性渐变
                                    var gradient = document.createElementNS('http://www.w3.org/2000/svg', 'linearGradient');
                                    var gradientId = 'gradient-' + i + '-' + (isActiveConnection ? 'active' : 'normal');
                                    gradient.setAttribute('id', gradientId);
                                    gradient.setAttribute('x1', '0%');
                                    gradient.setAttribute('y1', '0%');
                                    gradient.setAttribute('x2', '100%');
                                    gradient.setAttribute('y2', '0%');

                                    // 根据连接状态设置渐变色
                                    var startColor, endColor;
                                    if (isActiveConnection) {
                                        startColor = 'rgba(231, 76, 60, 0.8)';   // 活跃连接：半透明红色
                                        endColor = 'rgba(192, 57, 43, 0.9)';     // 到深红色
                                    } else {
                                        startColor = 'rgba(52, 152, 219, 0.6)';  // 普通连接：半透明蓝色
                                        endColor = 'rgba(41, 128, 185, 0.7)';    // 到深蓝色
                                    }

                                    var stop1 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
                                    stop1.setAttribute('offset', '0%');
                                    stop1.setAttribute('stop-color', startColor);

                                    var stop2 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
                                    stop2.setAttribute('offset', '70%');
                                    stop2.setAttribute('stop-color', endColor);

                                    var stop3 = document.createElementNS('http://www.w3.org/2000/svg', 'stop');
                                    stop3.setAttribute('offset', '100%');
                                    stop3.setAttribute('stop-color', startColor);

                                    gradient.appendChild(stop1);
                                    gradient.appendChild(stop2);
                                    gradient.appendChild(stop3);
                                    defs.appendChild(gradient);

                                    // 创建箭头标记
                                    var marker = document.createElementNS('http://www.w3.org/2000/svg', 'marker');
                                    var arrowId = 'arrow-' + i + '-' + (isActiveConnection ? 'active' : 'normal');

                                    marker.setAttribute('id', arrowId);
                                    marker.setAttribute('viewBox', '0 0 12 12');
                                    marker.setAttribute('refX', '11');
                                    marker.setAttribute('refY', '6');
                                    marker.setAttribute('markerWidth', '8');
                                    marker.setAttribute('markerHeight', '8');
                                    marker.setAttribute('orient', 'auto');
                                    marker.setAttribute('markerUnits', 'strokeWidth');

                                    // 创建箭头路径（改为更优雅的形状）
                                    var arrowPath = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                                    arrowPath.setAttribute('d', 'M2,2 L10,6 L2,10 L4,6 Z');  // 更优雅的箭头形状
                                    arrowPath.setAttribute('fill', 'url(#' + gradientId + ')');

                                    marker.appendChild(arrowPath);
                                    defs.appendChild(marker);
                                    svg.appendChild(defs);

                                    // 计算贝塞尔曲线控制点（可选：使用曲线让箭头更美观）
                                    var useCurve = Math.abs(dx) > 100; // 距离较远时使用曲线
                                    var pathData;

                                    if (useCurve) {
                                        // 修复：正确计算贝塞尔曲线控制点
                                        // 控制点应该在连线方向上偏移，而不是总是向右偏移
                                        var offsetX = dx * 0.3; // 保持dx的符号，确保控制点在正确方向
                                        var cp1x = x1 + offsetX;
                                        var cp1y = y1;
                                        var cp2x = x2 - offsetX;
                                        var cp2y = y2;

                                        // 对于水平线，添加一点垂直偏移让曲线更明显
                                        if (Math.abs(dy) < 1) {
                                            var verticalOffset = Math.min(Math.abs(dx) * 0.1, 20); // 最大20像素的垂直偏移
                                            cp1y = y1 - verticalOffset;
                                            cp2y = y2 - verticalOffset;
                                        }

                                        pathData = 'M' + x1 + ',' + y1 + ' C' + cp1x + ',' + cp1y + ' ' + cp2x + ',' + cp2y + ' ' + x2 + ',' + y2;
                                    } else {
                                        // 使用直线
                                        pathData = 'M' + x1 + ',' + y1 + ' L' + x2 + ',' + y2;
                                    }

                                    // 创建主路径
                                    var path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
                                    path.setAttribute('d', pathData);
                                    path.setAttribute('stroke', 'url(#' + gradientId + ')');
                                    path.setAttribute('stroke-width', strokeWidth);
                                    path.setAttribute('fill', 'none');
                                    path.setAttribute('stroke-linecap', 'round');
                                    path.setAttribute('stroke-linejoin', 'round');
                                    path.setAttribute('marker-end', 'url(#' + arrowId + ')');
                                    path.style.transition = 'all 0.4s cubic-bezier(0.4, 0, 0.2, 1)';

                                    // 添加交互效果
                                    path.style.cursor = 'pointer';
                                    path.style.pointerEvents = 'stroke';

                                    // 添加流动动画（可选）
                                    if (isActiveConnection) {
                                        var animationLength = length;
                                        path.style.strokeDasharray = '5 5';
                                        path.style.strokeDashoffset = '0';
                                        path.style.animation = 'flow-dash 2s linear infinite';
                                    }

                                    // 增强的悬停效果
                                    path.addEventListener('mouseenter', function() {
                                        this.setAttribute('stroke-width', parseFloat(strokeWidth) + 2);
                                        this.style.opacity = '1';

                                        // 添加脉冲动画
                                        this.style.animation = 'pulse-glow 1s ease-in-out infinite alternate';
                                    });

                                    path.addEventListener('mouseleave', function() {
                                        this.setAttribute('stroke-width', strokeWidth);
                                        this.style.opacity = '';

                                        // 恢复原始动画
                                        if (isActiveConnection) {
                                            this.style.animation = 'flow-dash 2s linear infinite';
                                        } else {
                                            this.style.animation = 'none';
                                        }
                                    });

                                    // 设置工具提示
                                    var title = document.createElementNS('http://www.w3.org/2000/svg', 'title');
                                    title.textContent = connection.source_node_name + '.' + connection.source_param_name + 
                                                      ' → ' + connection.target_node_name + '.' + connection.target_param_name;
                                    path.appendChild(title);

                                    svg.appendChild(path);

                                    // 添加箭头出现动画
                                    svg.style.animation = 'arrow-appear 0.6s cubic-bezier(0.4, 0, 0.2, 1) forwards';

                                    window.arrowContainer.appendChild(svg);
                                }
                            }
                        }
                    }

                    // 为所有pin添加事件监听器
                    for (var i = 0; i < pinElements.length; i++) {
                        var pin = pinElements[i];
                        pin.addEventListener('mouseenter', window.pinMouseEnter);
                        pin.addEventListener('mouseleave', window.pinMouseLeave);
                    }

                    console.log('Pin悬停事件监听器已设置，总pin数:', pinElements.length);

            } catch (error) {
                console.error('客户端回调错误:', error);
            }

            return window.dash_clientside.no_update;
        }
        """,
        Output("arrows-overlay-dynamic", "style"),
        Input("arrow-connections-data", "data"),
        Input("canvas-container", "children"),
        prevent_initial_call=True
    )


def register_dropdown_zindex_callback(app):
    """注册下拉菜单z-index管理回调"""
    app.clientside_callback(
        """
        function() {
            // 监听所有下拉菜单的显示/隐藏事件
            function setupDropdownListeners() {
                // 移除所有现有的监听器
                document.querySelectorAll('.dropdown-toggle').forEach(btn => {
                    btn.removeEventListener('click', handleDropdownToggle);
                });

                // 添加新的监听器
                document.querySelectorAll('.dropdown-toggle').forEach(btn => {
                    btn.addEventListener('click', handleDropdownToggle);
                });

                // 监听点击外部区域关闭下拉菜单
                document.addEventListener('click', handleOutsideClick);
            }

            function handleDropdownToggle(event) {
                const toggle = event.target.closest('.dropdown-toggle');
                const dropdown = toggle ? toggle.closest('.dropdown') : null;
                const nodeContainer = toggle ? toggle.closest('.node-container') : null;

                if (nodeContainer) {
                    // 重置所有节点的z-index
                    document.querySelectorAll('.node-container').forEach(node => {
                        node.classList.remove('dropdown-active');
                    });

                    // 立即提升当前节点的层级，不等待菜单显示
                    nodeContainer.classList.add('dropdown-active');
                }
            }

            function handleOutsideClick(event) {
                if (!event.target.closest('.dropdown')) {
                    // 如果点击在下拉菜单外部，重置所有节点的z-index
                    document.querySelectorAll('.node-container').forEach(node => {
                        node.classList.remove('dropdown-active');
                    });
                }
            }

            // 初始化监听器
            setupDropdownListeners();

            // 使用MutationObserver监听DOM变化，重新设置监听器
            const observer = new MutationObserver(function(mutations) {
                let needsUpdate = false;
                mutations.forEach(function(mutation) {
                    if (mutation.type === 'childList') {
                        mutation.addedNodes.forEach(function(node) {
                            if (node.nodeType === 1 && (
                                node.classList.contains('node-container') ||
                                node.querySelector('.dropdown-toggle')
                            )) {
                                needsUpdate = true;
                            }
                        });
                    }
                });
                if (needsUpdate) {
                    setTimeout(setupDropdownListeners, 100);
                }
            });

            observer.observe(document.body, {
                childList: true,
                subtree: true
            });

            return window.dash_clientside.no_update;
        }
        """,
        Output("canvas-container", "id"),  # 虚拟输出
        Input("canvas-container", "children")
    )


def register_theme_toggle_callback(app):
    """注册主题切换回调"""
    app.clientside_callback(
        """
        function(n_clicks) {
            if (n_clicks === null) {
                return window.dash_clientside.no_update;
            }

            const body = document.body;
            const isDark = n_clicks % 2 === 1;

            if (isDark) {
                body.setAttribute('data-theme', 'dark');
                localStorage.setItem('theme', 'dark');
            } else {
                body.removeAttribute('data-theme');
                localStorage.setItem('theme', 'light');
            }

            return window.dash_clientside.no_update;
        }
        """,
        Output("theme-toggle", "id"),  # 虚拟输出
        Input("theme-toggle", "n_clicks")
    )


def register_theme_restore_callback(app):
    """注册页面加载时恢复主题设置回调"""
    app.clientside_callback(
        """
        function() {
            const savedTheme = localStorage.getItem('theme');
            if (savedTheme === 'dark') {
                document.body.setAttribute('data-theme', 'dark');
            }
            return window.dash_clientside.no_update;
        }
        """,
        Output("theme-toggle", "title"),  # 虚拟输出
        Input("theme-toggle", "id")
    )


def register_all_clientside_callbacks(app):
    """注册所有客户端回调函数"""
    register_arrow_display_callback(app)
    register_dropdown_zindex_callback(app)
    register_theme_toggle_callback(app)
    register_theme_restore_callback(app) 