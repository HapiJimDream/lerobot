## 一、真实机器人场景（文档示例 / inference / il_robots / smolvla / rtc）


| #  | 英文任务描述                                          | 中文翻译                            | 来源          |
| -- | ----------------------------------------------------- | ----------------------------------- | ------------- |
| 1  | Pick up a Lego block and place it in a bin            | 拾取乐高积木并放入收纳箱            | il_robots.mdx |
| 2  | Grasp a lego block and put it in the bin              | 抓取乐高积木放入收纳箱              | smolvla.mdx   |
| 3  | Put lego brick into the box                           | 将乐高积木放入盒子                  | inference.mdx |
| 4  | Put lego brick into the transparent box               | 将乐高积木放入透明盒子              | il_robots.mdx |
| 5  | Pick up cube                                          | 拾取方块                            | inference.mdx |
| 6  | Pick up the cube                                      | 拾取该方块                          | inference.mdx |
| 7  | Pick up the red cube                                  | 拾取红色方块                        | inference.mdx |
| 8  | Grasp the block                                       | 抓取方块                            | inference.mdx |
| 9  | Move green small object into the purple platform      | 将绿色小物体移动到紫色平台上        | rtc.mdx       |
| 10 | Fold the T-shirt                                      | 折叠T恤                             | inference.mdx |
| 11 | Pick-place cube counting (5 positions × 10 episodes) | 拾放方块计数（5个位置 × 10次演示） | smolvla.mdx   |
| 12 | Pick-and-place of the lego block                      | 拾放乐高积木                        | smolvla.mdx   |

---

## 二、HIL-Serl / HiL 场景（hilserl.mdx）


| #  | 英文任务                                                    | 中文翻译             |
| -- | ----------------------------------------------------------- | -------------------- |
| 13 | Push cube to a goal region                                  | 将方块推至目标区域   |
| 14 | Pick and lift cube with the gripper                         | 用夹爪拾起并举起方块 |
| 15 | Pick and place cube                                         | 拾取并放置方块       |
| 16 | Bimanual tasks to pick objects with two arms                | 双臂拾取物体任务     |
| 17 | Hand-over tasks to transfer objects from one arm to another | 双臂传递物体任务     |
| 18 | pick_and_lift                                               | 拾取并抬起           |
| 19 | pick_and_place                                              | 拾取并放置           |

---

## 三、X-VLA 场景（xvla.mdx）


| #  | 英文任务                                   | 中文翻译                   |
| -- | ------------------------------------------ | -------------------------- |
| 20 | Folding cloths                             | 折叠布料                   |
| 21 | Bimanual handover cube                     | 双臂传递方块               |
| 22 | Pick-and-place on compact WidowX platforms | WidowX紧凑平台上的拾取放置 |

---

## 四、子任务分解示例（dataset_subtask.mdx）

完整任务："Pick up the apple and place it in the basket" → 拾取苹果放入篮子


| #  | 子任务             | 中文翻译   |
| -- | ------------------ | ---------- |
| 23 | Approach the apple | 接近苹果   |
| 24 | Grasp the apple    | 抓取苹果   |
| 25 | Lift the apple     | 抬起苹果   |
| 26 | Move to basket     | 移动到篮子 |
| 27 | Release the apple  | 释放苹果   |

---

## 五、RoboTwin 2.0 — 双臂 50 个任务（robotwin.mdx）

### 完整任务列表：


| #  | CLI 名称                    | 中文翻译                               | 类别      |
| -- | --------------------------- | -------------------------------------- | --------- |
| 1  | `adjust_bottle`             | 调整瓶子位置                           | 调整      |
| 2  | `beat_block_hammer`         | 用锤子敲击方块                         | 工具使用  |
| 3  | `blocks_ranking_rgb`        | 方块按颜色排序                         | 排序      |
| 4  | `blocks_ranking_size`       | 方块按大小排序                         | 排序      |
| 5  | `click_alarmclock`          | 按闹钟                                 | 精确按压  |
| 6  | `click_bell`                | 按铃铛                                 | 精确按压  |
| 7  | `dump_bin_bigbin`           | 将垃圾箱倒入大垃圾箱                   | 丢弃      |
| 8  | `grab_roller`               | 抓取滚筒                               | 抓取      |
| 9  | `handover_block`            | 双臂传递方块                           | 双臂协调  |
| 10 | `handover_mic`              | 双臂传递话筒                           | 双臂协调  |
| 11 | `hanging_mug`               | 悬挂马克杯                             | 悬挂      |
| 12 | `lift_pot`                  | 双臂抬起锅                             | 双臂搬运  |
| 13 | `move_can_pot`              | 将罐头移入锅中                         | 移动      |
| 14 | `move_pillbottle_pad`       | 将药瓶移至垫子上                       | 移动      |
| 15 | `move_playingcard_away`     | 移开扑克牌                             | 移动      |
| 16 | `move_stapler_pad`          | 将订书机移至垫子上                     | 移动      |
| 17 | `open_microwave`            | 打开微波炉                             | 关节物体  |
| 18 | `pick_diverse_bottles`      | 拾取多种瓶子                           | 抓取      |
| 19 | `pick_dual_bottles`         | 双臂拾取瓶子                           | 抓取      |
| 20 | `place_a2b_left`            | 从左臂将物体从A处放到B处               | 放置      |
| 21 | `place_a2b_right`           | 从右臂将物体从A处放到B处               | 放置      |
| 22 | `place_bread_basket`        | 将面包放入篮子                         | 放置      |
| 23 | `place_bread_skillet`       | 将面包放入煎锅                         | 放置      |
| 24 | `place_burger_fries`        | 放置汉堡和薯条                         | 放置      |
| 25 | `place_can_basket`          | 将罐头放入篮子                         | 放置      |
| 26 | `place_cans_plasticbox`     | 将罐头放入塑料箱                       | 放置      |
| 27 | `place_container_plate`     | 将容器放到盘子上                       | 放置      |
| 28 | `place_dual_shoes`          | 双臂放置鞋子                           | 放置      |
| 29 | `place_empty_cup`           | 放置空杯子                             | 放置      |
| 30 | `place_fan`                 | 放置风扇                               | 放置      |
| 31 | `place_mouse_pad`           | 将鼠标放到鼠标垫上                     | 放置      |
| 32 | `place_object_basket`       | 将物体放入篮子                         | 放置      |
| 33 | `place_object_scale`        | 将物体放到秤上                         | 放置      |
| 34 | `place_object_stand`        | 将物体放到支架上                       | 放置      |
| 35 | `place_phone_stand`         | 将手机放到手机支架上                   | 放置      |
| 36 | `place_shoe`                | 放置鞋子                               | 放置      |
| 37 | `press_stapler`             | 按订书机                               | 精确按压  |
| 38 | `put_bottles_dustbin`       | 将瓶子丢入垃圾桶                       | 丢弃      |
| 39 | `put_object_cabinet`        | 将物体放入柜子                         | 丢弃/收纳 |
| 40 | `rotate_qrcode`             | 旋转二维码                             | 旋转      |
| 41 | `scan_object`               | 扫描物体                               | 移动操作  |
| 42 | `shake_bottle`              | 摇晃瓶子                               | 连续运动  |
| 43 | `shake_bottle_horizontally` | 水平摇晃瓶子                           | 连续运动  |
| 44 | `stack_blocks_three`        | 堆叠三个方块                           | 堆叠      |
| 45 | `stack_blocks_two`          | 堆叠两个方块                           | 堆叠      |
| 46 | `stack_bowls_three`         | 堆叠三个碗                             | 堆叠      |
| 47 | `stack_bowls_two`           | 堆叠两个碗                             | 堆叠      |
| 48 | `stamp_seal`                | 盖章                                   | 精确放置  |
| 49 | `turn_switch`               | 转动开关                               | 关节物体  |
| 50 | `open_laptop`               | 打开笔记本电脑（上游有 bug，暂不可用） | 关节物体  |

---

## 六、VLABench — 43 个语言条件任务（vlabench.mdx）

### 基础任务（Primitive，21 个）


| #  | CLI 名称                | 中文翻译       |
| -- | ----------------------- | -------------- |
| 1  | `select_fruit`          | 选择水果       |
| 2  | `select_toy`            | 选择玩具       |
| 3  | `select_chemistry_tube` | 选择化学试管   |
| 4  | `add_condiment`         | 添加调味品     |
| 5  | `select_book`           | 选择书本       |
| 6  | `select_painting`       | 选择画作       |
| 7  | `select_drink`          | 选择饮品       |
| 8  | `insert_flower`         | 插入花朵       |
| 9  | `select_billiards`      | 选择台球       |
| 10 | `select_ingredient`     | 选择食材       |
| 11 | `select_mahjong`        | 选择麻将牌     |
| 12 | `select_poker`          | 选择扑克牌     |
| 13 | `density_qa`            | 密度问答       |
| 14 | `friction_qa`           | 摩擦力问答     |
| 15 | `magnetism_qa`          | 磁性问答       |
| 16 | `reflection_qa`         | 反射问答       |
| 17 | `simple_cuestick_usage` | 简单球杆使用   |
| 18 | `simple_seesaw_usage`   | 简单跷跷板使用 |
| 19 | `sound_speed_qa`        | 声速问答       |
| 20 | `thermal_expansion_qa`  | 热膨胀问答     |
| 21 | `weight_qa`             | 重量问答       |

### 复合任务（Composite，22 个）


| #  | CLI 名称                    | 中文翻译         |
| -- | --------------------------- | ---------------- |
| 22 | `cluster_billiards`         | 台球归组         |
| 23 | `cluster_book`              | 书本归组         |
| 24 | `cluster_drink`             | 饮品归组         |
| 25 | `cluster_toy`               | 玩具归组         |
| 26 | `cook_dishes`               | 烹饪菜肴         |
| 27 | `cool_drink`                | 冷藏饮料         |
| 28 | `find_unseen_object`        | 寻找不可见物体   |
| 29 | `get_coffee`                | 取咖啡           |
| 30 | `hammer_nail`               | 用锤子钉钉子     |
| 31 | `heat_food`                 | 加热食物         |
| 32 | `make_juice`                | 制作果汁         |
| 33 | `play_mahjong`              | 打麻将           |
| 34 | `play_math_game`            | 玩数学游戏       |
| 35 | `play_poker`                | 打扑克           |
| 36 | `play_snooker`              | 打斯诺克         |
| 37 | `rearrange_book`            | 重新排列书本     |
| 38 | `rearrange_chemistry_tube`  | 重新排列化学试管 |
| 39 | `set_dining_table`          | 布置餐桌         |
| 40 | `set_study_table`           | 布置书桌         |
| 41 | `store_food`                | 储存食物         |
| 42 | `take_chemistry_experiment` | 做化学实验       |
| 43 | `use_seesaw_complex`        | 复杂跷跷板操作   |

---

## 七、RoboCasa365 — 365 个厨房任务（robocasa.mdx）

### 原子任务（Atomic，~65 个）— 列出的示例


| # | CLI 名称                  | 中文翻译             |
| - | ------------------------- | -------------------- |
| 1 | `CloseFridge`             | 关闭冰箱             |
| 2 | `OpenDrawer`              | 打开抽屉             |
| 3 | `OpenCabinet`             | 打开橱柜             |
| 4 | `OpenBlenderLid`          | 打开搅拌机盖子       |
| 5 | `TurnOnMicrowave`         | 打开微波炉           |
| 6 | `TurnOffStove`            | 关闭炉灶             |
| 7 | `NavigateKitchen`         | 厨房导航             |
| 8 | `PickPlaceCounterToStove` | 从台面拾放物体到炉灶 |
| 9 | `PickPlaceCoffee`         | 拾放咖啡             |

### 复合任务类别（Composite，~300 个，60+ 子类别）


| #  | 英文类别           | 中文翻译     |
| -- | ------------------ | ------------ |
| 1  | Baking             | 烘焙         |
| 2  | Boiling            | 煮           |
| 3  | Brewing            | 冲泡         |
| 4  | Chopping           | 切菜         |
| 5  | Clearing table     | 清理桌面     |
| 6  | Defrosting food    | 解冻食物     |
| 7  | Loading dishwasher | 装洗碗机     |
| 8  | Making tea         | 泡茶         |
| 9  | Microwaving food   | 微波加热食物 |
| 10 | Washing dishes     | 洗碗         |

---

## 八、Meta-World — 50 个桌面操作任务（metaworld.mdx）

文档未列出所有 50 个具体任务名，仅提到：


| # | CLI 名称               | 中文翻译     | 难度   |
| - | ---------------------- | ------------ | ------ |
| 1 | `assembly-v3`          | 组装         | Medium |
| 2 | `dial-turn-v3`         | 转动表盘     | Medium |
| 3 | `handle-press-side-v3` | 侧面按压手柄 | Medium |

按难度分组：


| 难度      | 数量 | 中文翻译               |
| --------- | ---- | ---------------------- |
| Easy      | 28   | 简单（单步目标）       |
| Medium    | 11   | 中等（多步推理）       |
| Hard      | 6    | 困难（复杂接触）       |
| Very Hard | 5    | 非常困难（最具挑战性） |

---

## 九、LIBERO / LIBERO-plus — 130 个任务（libero.mdx / libero_plus.mdx）

按套件分组，具体任务名未逐一列出：


| # | 套件             | 任务数 | 中文翻译                      |
| - | ---------------- | ------ | ----------------------------- |
| 1 | `libero_spatial` | 10     | 空间关系推理任务              |
| 2 | `libero_object`  | 10     | 不同物体操作任务              |
| 3 | `libero_goal`    | 10     | 目标条件任务                  |
| 4 | `libero_90`      | 90     | 短时域操作任务                |
| 5 | `libero_10`      | 10     | 长时域链式任务（3-6个子目标） |

LIBERO-plus 在上述基础上施加 7 种扰动：


| # | 扰动维度              | 中文翻译       |
| - | --------------------- | -------------- |
| 1 | Camera viewpoints     | 相机视角       |
| 2 | Robot initial states  | 机器人初始状态 |
| 3 | Language instructions | 语言指令       |
| 4 | Light conditions      | 光照条件       |
| 5 | Background textures   | 背景纹理       |
| 6 | Sensor noise          | 传感器噪声     |

---

## 十、RoboMME — 16 个记忆操作任务（robomme.mdx）


| #  | 套件   | CLI 名称           | 中文翻译       |
| -- | ------ | ------------------ | -------------- |
| 1  | 计数   | `BinFill`          | 填满垃圾箱     |
| 2  | 计数   | `PickXtimes`       | 拾取X次        |
| 3  | 计数   | `SwingXtimes`      | 摆动X次        |
| 4  | 计数   | `StopCube`         | 停止方块       |
| 5  | 永久性 | `VideoUnmask`      | 视频揭示       |
| 6  | 永久性 | `VideoUnmaskSwap`  | 视频揭示交换   |
| 7  | 永久性 | `ButtonUnmask`     | 按钮揭示       |
| 8  | 永久性 | `ButtonUnmaskSwap` | 按钮揭示交换   |
| 9  | 引用   | `PickHighlight`    | 拾取高亮物体   |
| 10 | 引用   | `VideoRepick`      | 视频重选拾取   |
| 11 | 引用   | `VideoPlaceButton` | 视频放置按钮   |
| 12 | 引用   | `VideoPlaceOrder`  | 视频按顺序放置 |
| 13 | 模仿   | `MoveCube`         | 移动方块       |
| 14 | 模仿   | `InsertPeg`        | 插入圆柱销     |
| 15 | 模仿   | `PatternLock`      | 图案锁         |
| 16 | 模仿   | `RouteStick`       | 路线棒         |

---

## 十一、RoboCerebra — 长时域任务（robocerebra.mdx）

基于 LIBERO-10 长时域套件，每个 episode 链式组合 3-6 个子目标：


| # | 描述                                                           | 中文翻译                             |
| - | -------------------------------------------------------------- | ------------------------------------ |
| 1 | Long-horizon kitchen/living room tasks chaining 3–6 sub-goals | 长时域厨房/客厅任务，链接3-6个子目标 |

---

## 十二、IsaacLab Arena — 人形机器人任务（envhub_isaaclab_arena.mdx）


| # | 英文任务                       | 中文翻译            |
| - | ------------------------------ | ------------------- |
| 1 | Door opening                   | 开门                |
| 2 | Pick-and-place                 | 拾取放置            |
| 3 | Button pressing                | 按压按钮            |
| 4 | GR1 microwave manipulation     | GR1机器人微波炉操作 |
| 5 | G1 loco-manipulation           | G1机器人移动操作    |
| 6 | L90K1PutTheBlackBowlOnThePlate | 将黑碗放到盘子上    |

---

## 十三、动作表示文档（action_representations.mdx）


| # | 英文           | 中文翻译                           |
| - | -------------- | ---------------------------------- |
| 1 | Pick-and-place | 拾取放置（用于解释末端执行器空间） |

---

## 总计统计


| 来源                 | 任务数量                            |
| -------------------- | ----------------------------------- |
| 真实机器人场景示例   | 12                                  |
| HIL-Serl             | 7                                   |
| X-VLA                | 3                                   |
| 子任务分解           | 5                                   |
| **RoboTwin 2.0**     | **50**                              |
| **VLABench**         | **43**                              |
| **RoboCasa365**      | **365**（含9个示例 + 10个复合类别） |
| **Meta-World**       | **50**（含3个示例）                 |
| LIBERO / LIBERO-plus | 130（按套件）                       |
| RoboMME              | 16                                  |
| RoboCerebra          | 10（基于LIBERO-10）                 |
| IsaacLab Arena       | 6                                   |
| **总计**             | **~697+ 个任务**                    |

这是目前 LeRobot 文档中提及的所有任务的完整清单。如果你在设计 SmolVLA 多任务训练场景，建议优先参考 RoboTwin（双臂）和 VLABench（语言条件）的任务设计，它们与 SmolVLA 的能力最为匹配。
