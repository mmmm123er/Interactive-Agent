### 1. 状态查询
* 读取机器人本机状态、任务状态和运行健康
* 读取 active task、task stack 和 pending confirmation
* 读取地图 readiness、frame、版本
* 读取定位 readiness 和重定位置信信息
* 读取传感器流、帧率、延迟和 availability
* 读取全局/局部规划 readiness
* 读取 MCP 能力目录、边界和 deferred 能力
* legacy alias，不推荐新逻辑主动使用

### 2. 空间记忆与场景理解
* 根据自然语言目标查询语义路点候选
* 查询探索会话、路点数量、标签等摘要
* 获取当前场景采样状态和可用相机证据
* 请求当前位置 360 度语义观测
* 请求带 provenance 的语义记忆写入

### 3. 探索能力
* 请求自主探索或建图
* 请求停止探索
* 在探索过程中增量搜索缺失语义目标

### 4. 导航与局部运动能力
* 短距离相对运动，例如“前进三米”
* 到显式 map pose
* 到语义路点候选
* 跟随已规划路径引用
* 调整活动局部规划器速度偏好，不改变目标

### 5. 任务控制能力
确认待确认任务或探索决策
暂停 active task，并保存上下文
经过 policy 后恢复暂停任务
取消 active task 或 requested task
立即请求审计化停止运动