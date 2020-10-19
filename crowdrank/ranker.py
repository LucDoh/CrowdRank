from . import ingester
from . import interpreter
from . import postprocessing
from . import visualizer
from . import helpers


def rank(keyword, num_posts=500, skip=True):
    # Function that does end-to-end run
    use_s3 = helpers.in_S3()
    # 1) Ingest
    dh = ingester.DataHandler(keyword, num_posts=500, skip=skip, use_s3=use_s3)
    dh.get_recent_posts()
    # 2) Interpret
    comments = interpreter.get_and_interpret(dh.subreddits, keyword, use_s3=use_s3)
    # 3) Postprocessing
    df_ranking = postprocessing.postprocess(keyword, xref=True, use_s3=use_s3)
    df_ranking.index.name = "Brand"
    df_ranking.index = df_ranking.index.str.title()
    return df_ranking
