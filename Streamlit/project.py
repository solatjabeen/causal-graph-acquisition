import streamlit as st
import docx2txt
import pdfplumber
import spacy
import textacy
#import textacy.preprocessing
import textacy.resources
#import textacy.ke
import neuralcoref
from spacy.symbols import ORTH, POS, NOUN, VERB,PRON
import networkx as nx
from pyvis.network import Network
import matplotlib.pyplot as plt 
import streamlit.components.v1 as components

def load_image(image_file):
	img = Image.open(image_file)
	return img

def preprocess(narrative):
	nlp = spacy.load("en_core_web_sm")
	neuralcoref.add_to_pipe(nlp)
	narrative = textacy.preprocessing.normalize_quotation_marks(narrative)
	narrative = narrative.lower()
	narrative = nlp(narrative)
	narrative = narrative._.coref_resolved
	narrative = nlp(narrative)
	extractSVO(narrative)
	#return narrative

def extractSVO(narrative):
	finalList = []
	sentences = []
	ncl = []
	nncl = [()]
	checkPass = False
	rootCheck = False
	varForm1 = False
	varForm2 = False

	for sent in narrative.sents:
		for nc in sent.noun_chunks:
			ncl.append(nc)
		triplets = textacy.extract.subject_verb_object_triples(sent)
		triplets = list(triplets)
		if len(triplets)>0:
			for t in triplets:
				subject = t[0]
				objec = t[2]
				for chunk in ncl:
					for cToken in chunk:
						if str(cToken) == str(t[0]):
							subject = chunk
						if str(cToken) == str(t[2]):
							objec = chunk
				tup = (subject,t[1],objec)
				finalList.append(tup)
				sentences.append(sent)
			if len(ncl) == 3:
				nncl = [(ncl[0],triplets[0][1],ncl[1])]
				nncl.append((ncl[0],triplets[0][1],ncl[2]))
				finalList.append(nncl[0])
				sentences.append(sent)
				finalList.append(nncl[1])
				sentences.append(sent)
		else:
			for token in sent:
				if token.dep_ == 'nsubj':
					sub = token
				elif token.dep_ == 'nsubjpass':
					checkPass = True
					sub = token
				elif token.dep_ == 'ROOT':
					verb = token
					rootCheck = True
				elif token.pos_ == 'NOUN' and token.dep_ == 'conj':
					if rootCheck is True:
						varForm2 = True
					else:
						varForm1 = True
				else:
					if token.dep_ == 'dobj':
						obj = token
						continue
					elif token.dep_ == 'pobj':
						obj = token
						continue
			for nChunk in ncl:
				for nToken in nChunk:
					if str(nToken) == str(sub):
						sub = nChunk
						if str(nToken) == str(obj):
							obj = nChunk
			if checkPass is True:
				tuple = (obj,verb,sub)
			else:
				tuple = (sub,verb,obj)
			print("Triple by combining nsubj, root and dobj:")
			print(tuple)
			finalList.append(tuple)
			sentences.append(sent)
			if len(ncl) == 3:
				if varForm1 == True:
					nncl = [(ncl[0],verb,ncl[2])]
					nncl.append((ncl[1],verb,ncl[2]))
					finalList.append(nncl[0])
					sentences.append(sent)
					finalList.append(nncl[1])
					sentences.append(sent)
				else:
					nncl = [(ncl[0],verb,ncl[1])]
					nncl.append((ncl[0],verb,ncl[2]))
					finalList.append(nncl[0])
					sentences.append(sent)
					finalList.append(nncl[1])
					sentences.append(sent)
		ncl.clear()
		nncl.clear()
		rootCheck = False
		checkPass = False
		varForm1 = False
		varForm2 = False
	trips = finalList
	KnowledgeGraph(trips)

def KnowledgeGraph(trips):
	nt = Network("500px", "1000px", notebook=True,directed=True, bgcolor='#ffffff', font_color='black', layout=None, heading='Knowledge Graph')
	for dm in trips:
		nt.add_node(str(dm[0]),shape = 'box',physics='false',color = "#ffffff")
		nt.add_node(str(dm[2]),shape = 'box',physics='false',color = "#ffffff")
		nt.add_edge(str(dm[0]),str(dm[2]),label=str(dm[1]), weight=10, physics='false',color='black')
	nt.set_edge_smooth('discrete')
	#nt.show("./Pyvis Graph/Causal Graph.html")
	try:
		path = '/tmp'
		nt.save_graph(f'{path}/Knowledge Graph.html')
		HtmlFile = open(f'{path}/Knowledge Graph.html', 'r', encoding='utf-8')
	except:
		path = './'
		nt.save_graph(f'{path}/Knowledge Graph.html')
		HtmlFile = open(f'{path}/Knowledge Graph.html', 'r', encoding='utf-8')
	components.html(HtmlFile.read(), width=700,height=1000)


def main():
	st.title("Causal Graph Aquisition")

	#menu = ["Image","Dataset","DocumentFiles","About"]
	#choice = st.sidebar.selectbox("Menu",menu)

	#if choice == "DocumentFiles":
	#st.subheader("DocumentFiles")
	docx_file = st.file_uploader("Upload Document", type=["pdf","docx","txt"])
		
	if st.button("Process"):

		if docx_file is not None:

			#file_details = {"filename":docx_file.name, "filetype":docx_file.type,
            #                    "filesize":docx_file.size}
			#st.write(file_details)

			if docx_file.type == "text/plain":
				# Read as string (decode bytes to string)
				raw_text = str(docx_file.read(),"utf-8")
				st.text(raw_text)
				preprocess(raw_text)

			elif docx_file.type == "application/pdf":
				try:
					with pdfplumber.open(docx_file) as pdf:
						pages = pdf.pages[0]
						st.write(pages.extract_text())
				except:
					st.write("None")
			else:
				raw_text = docx2txt.process(docx_file)
				st.write(raw_text)
				
				
				

if __name__ == '__main__':
	main()