#!/usr/bin/env python3
import json
import pprint
import re
import requests

skipList = ['Times Counted', 'Registered Voters', 'Number of Precincts for Race', 'Number of Precincts Reporting']

def total_votes(total, locality):
	for race in locality:
		if race == 'Race Statistics':
			continue
		if race not in total:
			total[race] = {}
		if 'YES' in locality[race]:
			if 'YES' not in total[race]:
				total[race] = {'YES': 0, 'NO': 0 }
			total[race]['YES'] += locality[race]['YES']
			total[race]['NO'] += locality[race]['NO']
		elif race not in skipList:
			for candidate in locality[race]:
				if candidate not in skipList:
					if candidate not in total[race]:
						total[race][candidate] = {}
					((party, votes),) = locality[race][candidate].items()
					if party not in total[race][candidate]:
						total[race][candidate][party] = 0
					total[race][candidate][party] += votes

def sum_votes(stateData):
	stateData.update({'Overall Totals': {}})
	stateTotal = {}
	for district in stateData:
		stateTotal[district] = {}
		districtTotal = stateTotal[district]
		if district == 'Overseas':
			total_votes(districtTotal, stateData[district])
			continue
		for ballotType in stateData[district]:
			if ballotType == 'Precincts':
				for precinct in stateData[district][ballotType]:
					total_votes(districtTotal, stateData[district][ballotType][precinct])
			else:
				total_votes(districtTotal, stateData[district][ballotType])
		stateData[district]['Totals'] = {}
		stateData[district]['Totals'].update(districtTotal)
	for district in stateTotal:
		total_votes(stateData['Overall Totals'], stateTotal[district])
	del stateData['Overall Totals']['Totals']

def organize_localities(locality, stateData):
	if locality == 'HD99 Fed Overseas Absentee':
		stateData['Overseas'] = {}
		return stateData['Overseas']
	if locality[0] == 'D':
		if locality[10] == ' ':
			district = '0' + locality[9]
			name = locality[13:]
		else:
			district = locality[9:11]
			name = locality[14:]	
		districtName = 'District ' + district
		stateData[districtName] = stateData.get(districtName, {'Totals': {}})		
		stateData[districtName][name] = {}
		return stateData[districtName][name]
	else:
		districtNumber = locality[:2]
		name = locality[3:]
		districtName = 'District ' + districtNumber
		stateData[districtName] = stateData.get(districtName, {'Totals': {}})
		stateData[districtName]['Precincts'] = stateData[districtName].get('Precincts', {})
		stateData[districtName]['Precincts'][name] = {}
		return stateData[districtName]['Precincts'][name]

def process_data(data):
	stateData = {}
	for locality in data:
		localDict = organize_localities(locality.strip(), stateData)
		localDict.update(data[locality])
	sum_votes(stateData)
	return stateData

def list_to_nest(arr, nest):
	if not arr:
		return
	if arr[0] not in nest:
		nest[arr[0]] = {}
	if len(arr) == 2:
		val = arr[1]
		try:
			val = int(val)
		except TypeError:
			pass
		nest[arr[0]] = val
		return
	list_to_nest(arr[1:], nest[arr[0]])

def main():
	data = {}
	for line in requests.get('https://www.elections.alaska.gov/results/20GENR/resultsbyprecinct.txt').text.strip().replace('"', '').split('\n'):
		cols = re.sub('\s+',' ', line.strip().strip(',')).split(',')
		list_to_nest([col for ind, col in enumerate(cols) if ind in [0, 1, 4, 5, 7] and col and col != 'NP'], data)
	
	stateData = process_data(data)

	with open('akElectionResults2020.json', 'w') as json_file:
		json.dump(stateData, json_file)

if __name__ == '__main__':
	main()
