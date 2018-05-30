## suboptimal, but fast, implementation of the corehd and weak-neighbor algorithm ##
## The code can be implemented by hirarchical binning, eading to better time complexity ##

import sys
import networkx as nx
from random import *


def score(v,G,scm='HD'):
	# compute the score of node v in G

	if scm == 'HD':
	# high degree score : uniform
		scr = 0
	elif scm == 'WN':
	# weak-neighbor1 score
		scr = sum( (G.degree(nb) for nb in G[v]) )
		scr = - scr
	elif scm == 'SN':
	# weak-neighbor2 score
		if G.degree(v) != 0:
			scr = sum( (G.degree(nb) for nb in G[v]) )
			scr = G.degree(v) - scr/float(G.degree(v))
		else:
			scr = 0
	else:
		sys.exit("Error : score function is not defined.")

	return scr

def category(v,k,G,scm='HD'):
	# computes the right category to order node to
	if scm == 'HD':
		dgr = max(k-1,G.degree(v))
	elif scm == 'WN':
		dgr = max(k-1,G.degree(v))
	elif scm == 'SN':
		if G.degree(v) < k:
			dgr = k-1
		else:
			dgr = k
	else:
		sys.exit("Error : algorithm is not defined.")

	return dgr

def max_cat(k,G,scm='HD'):
	# computes the max category in dict
	if scm == 'HD':
		out = max(G.degree().values())
	elif scm == 'WN':
		out = max(G.degree().values())
	elif scm == 'SN':
		out = k
	else:
		sys.exit("Error : algorithm is not defined. Cannot obtain max.")

	return out

def preprocess(k,G,scm='HD'):
	# suboptimal, but O(|G|), computation of some initial properties

	# size of initial graph
	N0 = len(G)
	# compute the k-core in O(|G|) steps (not really necessary)
	G = nx.k_core(G,k)
	# size of the initial k-core
	N = len(G)
	
	# if the core is empty we are done
	if N == 0:
		return G, 0, dict(), dict(), dict(), N0, N

	dmax = max_cat(k,G,scm)

	# Initialize the dictionary, H, with 
	# H[degree][score] = {i_1: 1, ..., i_r:1} and i_j indicating a node
	# degree = k-1,...,d because it is not necessary to distinguish nodes of degree smaller k.
	# the k-1 nodes need not be organized by score, but it makes the code less prune to errors and doesn't cost us much
	H = { d: dict() for d in range(k-1,dmax+1) }
	
	# collect the score for every node 
	score_dict = {}
	# collect the max score for each 'degree' = k-1
	max_score_dict = {}

	for v in G.nodes():
		dgr = category(v,k,G,scm)
		scr = score(v,G,scm)
		score_dict[v] = scr
		# sort them in dictionaries by scores.
		try:
			H[dgr][scr][v] = 1
		except KeyError:
			# create if it does not already exist
			H[dgr][scr] = dict()
			H[dgr][scr][v] = 1

	# track currently largest score for each H[.] 
	for sub_dict_name in H.keys():
		try:
			mx_scr = max(H[sub_dict_name].keys())
		except ValueError:
			mx_scr = None 

		max_score_dict[sub_dict_name] = mx_scr


	return G, dmax, H, max_score_dict, score_dict, N0, N

#### JUST ADAPT d \in {<k or >k} for SN
def destroy(k,G,scm='HD'):
	# implementation of the generalized corehd algorithm (scm='HD')
	# and one version of the weak-neighbor algorithm (scm='WN')
	# we assume that G has no self-loops.

	### initialize 
	# pre-processing
	G, dmax, H, max_score_dict, score_dict, N0, N = preprocess(k,G,scm)
	# set of seeds
	D = []
	if N == 0:
		return D
	# current indicator for either removal (d=dmax) or trimming (d=k-1)
	if max_score_dict[k-1] == None:
		d = dmax
	else:
		d = k-1

	### remove and trimm until the k-core is empty
	cnt = 0 ; done = False ;
	while cnt < N and done == False: 
		cnt += 1

		## remove node 

		# get the max score of degree d nodes
		mx_scr_d = max_score_dict[d]

		# remove one of them at random
		v = choice(H[d][mx_scr_d].keys())

		# if d > k-1 add them to the seed set
		if d >= k:
			D.append(v)

		# remove element from H and set its score to None
		del H[d][mx_scr_d][v]
		score_dict[v] = None

		# check for newest largest score
		if H[d][mx_scr_d] == {}:
			del H[d][mx_scr_d]
		# update max_score_dict
		# suboptimal
		try:
			max_score_dict[d] = max(H[d].keys())
		except ValueError:
			max_score_dict[d] = None

		## update the neighbors 
		dv = G[v]
		ddv = set()
		# remove neighbors from dict (for now)
		# other cases we will take care of below. E.g. updating max_score of the new degree
		for nb in dv:
			remove_node_by_score(nb,G,H,max_score_dict,score_dict,k,scm)
			ddv = ddv | set(G[nb].keys())
		
		# remove also neighbors neighbors (except v) because their score will change
		ddv = ddv - set([v])
		ddv = ddv - set(dv)
		for nnb in ddv:
			remove_node_by_score(nnb,G,H,max_score_dict,score_dict,k,scm)

		## remove v from G
		G.remove_node(v)
		
		# update the degrees of the neighbors and their scores
		for nb in dv:
			add_node_by_score(nb,G,H,max_score_dict,score_dict,k,scm)
		# update scores of the neighbors neighbors
		for nnb in ddv:
			add_node_by_score(nnb,G,H,max_score_dict,score_dict,k,scm)

		## check if dmax needs updating and do so if necessary. not necessary
		if max_score_dict[d] == None:
			# attempt to update
			try: 
				while max_score_dict[dmax] == None:
					dmax -= 1
			# unless there are no nodes left
			except KeyError:
				done = True
				#sys.exit('Error!')

		## update d
		if max_score_dict[k-1] != None:
			d = k-1
		else:
			d = dmax


	return D, N 


def add_node_by_score(v,G,H,max_score_dict,score_dict,k,scm):
	# get new score
	score_dict[v] = score(v,G,scm)
	# get new category (degree) for dict reordering
	dgr = category(v,k,G,scm)
	# insert into proper spot
	try:
		H[dgr][score_dict[v]][v] = 1
	except KeyError:
		# create if it does not already exist
		H[dgr][score_dict[v]] = dict()
		H[dgr][score_dict[v]][v] = 1
	# update max_score
	if max_score_dict[dgr] == None or max_score_dict[dgr] < score_dict[v]:
		max_score_dict[dgr] = score_dict[v]

def remove_node_by_score(v,G,H,max_score_dict,score_dict,k,scm):
	# find the right dict
	dgr = category(v,k,G,scm)
	# remove the current nb
	del H[dgr][score_dict[v]][v]
	# if there are no more nodes of this particular score, remove the dict
	if H[dgr][score_dict[v]] == {}:
		del H[dgr][score_dict[v]]
	# if the score was equal to the max score, update max_score_dict
	if score_dict[v] == max_score_dict[dgr]:
		try:
			max_score_dict[dgr] = max(H[dgr].keys())
		# no more nodes left of degree d
		except ValueError:
			max_score_dict[dgr] = None


if __name__ == "__main__":
	_ = 0

