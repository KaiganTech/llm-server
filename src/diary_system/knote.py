import json
import datetime
import os
from typing import List, Dict, Any

class DiarySystem:
    def __init__(self, data_file="diary_data.json"):
        self.data_file = data_file
        self.entries = self.load_data()
    
    def load_data(self) -> List[Dict[str, Any]]:
        """加载日记数据"""
        if os.path.exists(self.data_file):
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []
    
    def save_data(self):
        """保存日记数据"""
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(self.entries, f, ensure_ascii=False, indent=2)
    
    def add_entry(self, entry_type: str, content: str, tags: List[str] = None, mood: str = None):
        """添加日记条目
        
        Args:
            entry_type: 条目类型 (activity/event/profile)
            content: 内容
            tags: 标签列表
            mood: 心情状态
        """
        entry = {
            "id": len(self.entries) + 1,
            "type": entry_type,
            "content": content,
            "tags": tags or [],
            "mood": mood,
            "date": datetime.datetime.now().strftime("%Y-%m-%d")
        }
        self.entries.append(entry)
        self.save_data()
        print(f"日记条目已添加 (ID: {entry['id']})")
    
    def search_entries(self, keyword: str = None, entry_type: str = None, 
                      tags: List[str] = None, date: str = None) -> List[Dict[str, Any]]:
        """搜索日记条目
        
        Args:
            keyword: 关键词
            entry_type: 条目类型
            tags: 标签列表
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            匹配的日记条目列表
        """
        results = self.entries.copy()

        if date:
            results = [entry for entry in results if entry['date'] == date]

        if entry_type:
            results = [entry for entry in results if entry['type'] == entry_type]

        if tags:
            results = [entry for entry in results 
                      if any(tag in entry['tags'] for tag in tags)]
        
        if keyword:
            results = [entry for entry in results 
                      if keyword.lower() in entry['content'].lower()]
    
        return sorted(results, key=lambda x: x['date'], reverse=True)

    def display_entry(self, entry: Dict[str, Any]):
        """显示单个日记条目"""
        print(f"\n{'='*50}")
        print(f"ID: {entry['id']}")
        print(f"类型: {entry['type']}")
        print(f"日期: {entry['date']}")
        if entry['mood']:
            print(f"心情: {entry['mood']}")
        if entry['tags']:
            print(f"标签: {', '.join(entry['tags'])}")
        print(f"\n内容:\n{entry['content']}")
        print(f"{'='*50}")
    
    def display_summary(self):
        """显示日记摘要"""
        print(f"\n日记系统摘要")
        print(f"总条目数: {len(self.entries)}")
        
        type_counts = {}
        for entry in self.entries:
            type_counts[entry['type']] = type_counts.get(entry['type'], 0) + 1
        
        for entry_type, count in type_counts.items():
            print(f"{entry_type}类条目: {count}个")
        
        if self.entries:
            latest = max(self.entries, key=lambda x: x['date'])
            print(f"最新条目: {latest['title']} ({latest['date']})")

def main():
    diary = DiarySystem()
    
    while True:
        print(f"\n{'='*30}")
        print("个人日记系统")
        print("1. 添加日记条目")
        print("2. 搜索日记条目")
        print("3. 显示所有条目")
        print("4. 显示系统摘要")
        print("5. 退出")
        print(f"{'='*30}")
        
        choice = input("请选择操作 (1-5): ").strip()
        
        if choice == '1':
            print("\n添加新日记条目")
            print("类型选项: activity(个人活动), event(重大事件), profile(基础信息)")
            
            entry_type = input("条目类型: ").strip()
            content = input("内容: ").strip()
            tags_input = input("标签 (用逗号分隔): ").strip()
            tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else []
            mood = input("心情状态 (可选): ").strip() or None
            
            diary.add_entry(entry_type, content, tags, mood)
        
        elif choice == '2':
            print("\n搜索日记条目")
            print("留空表示不限制该条件")
            
            keyword = input("关键词: ").strip() or None
            entry_type = input("类型: ").strip() or None
            tags_input = input("标签 (用逗号分隔): ").strip()
            tags = [tag.strip() for tag in tags_input.split(',')] if tags_input else None
            date = input("日期 (YYYY-MM-DD): ").strip() or None
            
            results = diary.search_entries(keyword, entry_type, tags, date)
            
            if results:
                print(f"\n找到 {len(results)} 个匹配的条目:")
                for entry in results:
                    diary.display_entry(entry)
            else:
                print("未找到匹配的条目")
        
        elif choice == '3':
            print("\n所有日记条目:")
            if diary.entries:
                for entry in sorted(diary.entries, key=lambda x: x['timestamp'], reverse=True):
                    diary.display_entry(entry)
            else:
                print("暂无日记条目")
        
        elif choice == '4':
            diary.display_summary()
        
        elif choice == '5':
            print("感谢使用日记系统，再见！")
            break
        
        else:
            print("无效选择，请重新输入")

if __name__ == "__main__":
    main()