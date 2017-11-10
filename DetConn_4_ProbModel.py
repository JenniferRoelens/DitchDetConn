'''
Created in 2017
@author: Jennifer Roelens

# Run this file only after adapting the possible connection file with the ground truth
'''

import DetConn_Pred as pred
import numpy
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import RFECV, RFE
#from sklearn.linear_model import LogisticRegression
import statsmodels.api as sm
from sklearn.metrics import confusion_matrix

'''
CODE
'''

# Retrieve predictor variables
#-----------------------------
predconn = pred.predconn
varnames = ['length', 'slope', 'dangle', 'orient', 'profcurv_mean', 'profcurv_std', 'profcurv_var', 'profcurv_rng', 'tancurv_mean',
            'tancurv_std', 'tancurv_var', 'tancurv_rng', 'fill_mean', 'fill_std', 'fill_var', 'fill_rng', 'rea_mean',
            'rea_std', 'rea_var', 'rea_rng', 'int_mean', 'int_std', 'int_var', 'int_rng', 'r_mean', 'r_std', 'r_var',
            'r_rng', 'g_mean', 'g_std', 'g_var', 'g_rng', 'b_mean', 'b_std', 'b_var', 'b_rng']

# Select random training and validation dataset
#----------------------------------------------

print 'Create training and validation datasets'
# 35 variables & 1 undependend var
X = predconn[:,0:36]
y = predconn[:,36]

# RFE selection and logistic regression'
#---------------------------------------

print 'RFE selection and logistic regression'

try: 
    ranfor = RandomForestClassifier(min_samples_leaf = 5, class_weight = 'balanced', n_estimators = 100)
    rf = ranfor.fit(X,y)
    selector = RFECV(rf)
    selector = selector.fit(X, y)
    varrf = numpy.asarray(varnames)[selector.support_]
    ind = []
    for i in varrf:
        idx = numpy.where(numpy.array(varnames)==i)
        ind = numpy.append(ind,idx)
    ind = ind.astype(int)
    Xrec = X[:,ind]
    logit = sm.Logit(y, Xrec)
    result = logit.fit()
    print result.summary()
    varrf_sig = varrf[result.pvalues < 0.05]
    print varrf_sig
except numpy.linalg.linalg.LinAlgError as err:
    ranfor = RandomForestClassifier(min_samples_leaf = 5, class_weight = 'balanced', n_estimators = 100)
    rf = ranfor.fit(X,y)
    selector = RFE(rf,10)
    selector = selector.fit(X, y)
    varrf = numpy.asarray(varnames)[selector.support_]
    print varrf
ind = []
for i in varrf:
    idx = numpy.where(numpy.array(varnames)==i)
    ind = numpy.append(ind,idx)
ind = ind.astype(int)
Xrec = X[:,ind]
logmodel = sm.Logit(y, Xrec)
result = logmodel.fit()
print result.summary()

# Validation
#-----------
 
cut_off = sum(y)/len(y)
#cut_off = 0.33
accuracy = numpy.zeros(10)
error_omission = numpy.zeros(10)
error_commission = numpy.zeros(10)
llr_p = numpy.zeros(10)
for i in range(0,10):
    sample_rows = numpy.random.choice(numpy.arange(len(predconn)), int(0.9 * len(predconn)), replace=False)
    val_rows = numpy.setdiff1d(numpy.union1d(sample_rows, numpy.arange(len(predconn))), numpy.intersect1d(sample_rows, numpy.arange(len(predconn))))
    datasample = predconn[sample_rows,:]
    valsample = predconn[val_rows,:]
    # 35 variables & 1 undependend var
    Xtrain = datasample[:,0:36]
    ytrain = datasample[:,36]
    ytrain.astype(int)
    Xval = valsample[:,0:36]
    yval = valsample[:,36]
    yval.astype(int)
    print 'Validate'
    # model
    logmodeltrain = sm.Logit(ytrain, Xtrain[:,ind])
    resulttrain = logmodeltrain.fit()
    print resulttrain.summary()
    # predict
    predictions_prob = resulttrain.predict(Xval[:,ind])
    predictions = []
    for prob in predictions_prob:
        if prob > cut_off:
            predic = 1
        else: predic = 0
        predictions = numpy.append(predictions, predic)
    conf = confusion_matrix(yval, predictions)
    accuracy[i] = float(conf[0,0] + conf[1,1])/len(Xval)
    error_omission[i] = conf[1,0]/float(conf[1,0] + conf[0,0])
    error_commission[i] = conf[0,1]/float(conf[0,1] + conf[1,1])
    llr_p[i] = resulttrain.llr_pvalue
    print "accuracy = " + str(accuracy)
    print "error of omission = " + str(error_omission)
    print "error of commission = " + str(error_commission)
print "avg accuracy = " + str(numpy.nanmean(accuracy))
print "avg om = " + str(numpy.nanmean(error_omission))
print "avg com = " + str(numpy.nanmean(error_commission))
print "avg_pv_llr = " + str(numpy.average(llr_p))

print "Finished"