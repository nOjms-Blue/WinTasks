from typing import TypedDict, Literal
import time
import datetime
import subprocess
import csv

TAB_SIZE: int = 8

class TaskData(TypedDict):
	ImageName: str
	PID: int
	SessionName: str
	SessionNumber: int
	MemUsage: str

def tasklist() -> list[TaskData]:
	result = subprocess.run(["tasklist", "/FO", "CSV", "/FI", "STATUS eq running", "/NH"], capture_output=True, text=True)
	lines = result.stdout.splitlines()
	
	tasks: list[TaskData] = []
	reader = csv.reader(lines)
	for row in reader:
		task: TaskData = {
			"ImageName": row[0],
			"PID": int(row[1]),
			"SessionName": row[2],
			"SessionNumber": int(row[3]),
			"MemUsage": row[4],
		}
		tasks.append(task)
	
	return tasks

class TaskDiff(TypedDict):
	Status: Literal["added", "removed", "changed"]
	ImageName: str
	PID: int
	SessionName: str
	SessionNumber: int
	MemUsage: str

def diff_tasklist(before: list[TaskData], after: list[TaskData]) -> list[TaskDiff]:
	diffs: list[TaskDiff] = []
	before_tasks: dict[str, TaskData] = {}
	after_tasks: dict[str, TaskData] = {}

	for task in before:
		before_tasks[f"{str(task["PID"])}@{task["ImageName"].replace("@", "@@")}"] = task

	for task in after:
		after_tasks[f"{str(task["PID"])}@{task["ImageName"].replace("@", "@@")}"] = task
	
	tasks: list[str] = list(before_tasks.keys()) + list(after_tasks.keys())
	
	for task_key in tasks:
		if task_key not in before_tasks:
			diffs.append({
				"Status": "added",
				"ImageName": after_tasks[task_key]["ImageName"],
				"PID": after_tasks[task_key]["PID"],
				"SessionName": after_tasks[task_key]["SessionName"],
				"SessionNumber": after_tasks[task_key]["SessionNumber"],
				"MemUsage": after_tasks[task_key]["MemUsage"],
			})
		elif task_key not in after_tasks:
			diffs.append({
				"Status": "removed",
				"ImageName": before_tasks[task_key]["ImageName"],
				"PID": before_tasks[task_key]["PID"],
				"SessionName": before_tasks[task_key]["SessionName"],
				"SessionNumber": before_tasks[task_key]["SessionNumber"],
				"MemUsage": before_tasks[task_key]["MemUsage"],
			})
		else:
			if before_tasks[task_key]["MemUsage"] != after_tasks[task_key]["MemUsage"]:
				diffs.append({
					"Status": "changed",
					"ImageName": after_tasks[task_key]["ImageName"],
					"PID": after_tasks[task_key]["PID"],
					"SessionName": after_tasks[task_key]["SessionName"],
					"SessionNumber": after_tasks[task_key]["SessionNumber"],
					"MemUsage": after_tasks[task_key]["MemUsage"],
				})
	
	return diffs

def adjust_tab(text: str) -> str:
	text_list = text.split("\t")
	result: str = text_list[0]
	
	for t in text_list[1:]:
		length = len(result)
		size = length % TAB_SIZE
		result += (" " * (TAB_SIZE - size)) + t
	
	return result

def main():
	before = tasklist()
	while(True):
		after = tasklist()
		
		if before != after:
			now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
			diffs = diff_tasklist(before, after)
			
			for diff in diffs:
				if diff["Status"] == "changed":
					continue
				
				status = " "
				if diff["Status"] == "added":
					status = "+"
				elif diff["Status"] == "removed":
					status = "-"
				
				print(adjust_tab(f"{now}  {status} {diff['ImageName']}\tPID:{diff['PID']}"))
			
			before = after
		
		time.sleep(0.25)

if __name__ == "__main__":
	try:
		main()
	except KeyboardInterrupt:
		pass
