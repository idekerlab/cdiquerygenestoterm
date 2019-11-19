FROM continuumio/miniconda3


RUN mkdir /tmp/cdiquery
COPY dist/*.whl /tmp/cdiquery/

RUN pip install /tmp/cdiquery/cdiquerygenestoterm*whl

RUN rm -rf /tmp/cdiquery

ENTRYPOINT ["/opt/conda/bin/cdiquerygenestotermcmd.py"]
CMD ["--help"]
