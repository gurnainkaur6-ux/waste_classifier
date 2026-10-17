"""
train_advanced.py
-----------------
Production-grade ML training with proper evaluation, baselines, and visualization.

Features:
- Baseline comparisons (majority class, single feature, all features)
- Cross-validation with confidence intervals
- Learning curves (train/test accuracy over time)
- Confusion matrices with visualization
- Feature importance analysis
- Calibration plots
- Comprehensive metrics report

Run:
    python train_advanced.py

Outputs:
- models/*.joblib (trained pipelines)
- models/model_comparison.json (metrics)
- models/evaluation_report.json (detailed analysis)
- models/plots/*.png (visualizations)
"""
import json
import os
import warnings
from collections import Counter

import joblib
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend for server environments
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import (accuracy_score, confusion_matrix, f1_score,
                             precision_score, recall_score, roc_auc_score,
                             classification_report)
from sklearn.model_selection import (cross_val_score, learning_curve,
                                    StratifiedKFold, train_test_split)
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, label_binarize
from sklearn.svm import SVC
from sklearn.tree import DecisionTreeClassifier

warnings.filterwarnings('ignore')
sns.set_style("whitegrid")

RANDOM_STATE = 42
FEATURES = ["material_type", "wet_or_dry", "texture", "biodegradable"]
TARGET = "category"


def build_pipeline(model, features=None):
    """Build a pipeline with one-hot encoding and the given model."""
    if features is None:
        features = FEATURES
    encoder = ColumnTransformer(
        [("onehot", OneHotEncoder(handle_unknown="ignore"), features)]
    )
    return Pipeline([("encode", encoder), ("model", model)])


def confidence_interval(accuracy, n_samples, confidence=0.95):
    """Calculate Wilson score confidence interval for accuracy."""
    from scipy import stats
    z = stats.norm.ppf((1 + confidence) / 2)
    
    p = accuracy
    n = n_samples
    
    denominator = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denominator
    margin = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denominator
    
    return max(0, center - margin), min(1, center + margin)


def plot_confusion_matrix(cm, labels, title, filename):
    """Save confusion matrix heatmap."""
    plt.figure(figsize=(10, 8))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=labels, yticklabels=labels,
                cbar_kws={'label': 'Count'})
    plt.title(title, fontsize=14, fontweight='bold')
    plt.ylabel('True Label', fontsize=12)
    plt.xlabel('Predicted Label', fontsize=12)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {filename}")


def plot_learning_curve(estimator, X, y, title, filename):
    """Plot and save learning curve."""
    train_sizes, train_scores, test_scores = learning_curve(
        estimator, X, y, cv=5, n_jobs=-1, 
        train_sizes=np.linspace(0.1, 1.0, 10),
        random_state=RANDOM_STATE, shuffle=True
    )
    
    train_mean = np.mean(train_scores, axis=1)
    train_std = np.std(train_scores, axis=1)
    test_mean = np.mean(test_scores, axis=1)
    test_std = np.std(test_scores, axis=1)
    
    plt.figure(figsize=(10, 6))
    plt.plot(train_sizes, train_mean, 'o-', color='r', label='Training score')
    plt.plot(train_sizes, test_mean, 'o-', color='g', label='Cross-validation score')
    
    plt.fill_between(train_sizes, train_mean - train_std, train_mean + train_std, 
                     alpha=0.1, color='r')
    plt.fill_between(train_sizes, test_mean - test_std, test_mean + test_std, 
                     alpha=0.1, color='g')
    
    plt.xlabel('Training Set Size', fontsize=12)
    plt.ylabel('Accuracy', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.legend(loc='lower right')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {filename}")


def plot_feature_importance(importance, feature_names, title, filename):
    """Plot and save feature importance."""
    indices = np.argsort(importance)[::-1]
    
    plt.figure(figsize=(10, 6))
    plt.bar(range(len(importance)), importance[indices], color='steelblue', alpha=0.8)
    plt.xticks(range(len(importance)), [feature_names[i] for i in indices], rotation=45, ha='right')
    plt.xlabel('Features', fontsize=12)
    plt.ylabel('Importance', fontsize=12)
    plt.title(title, fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {filename}")


def plot_calibration_curve(y_true, y_prob, title, filename):
    """Plot and save calibration curve for binary problems."""
    try:
        fraction_of_positives, mean_predicted_value = calibration_curve(
            y_true, y_prob, n_bins=10, strategy='uniform'
        )
        
        plt.figure(figsize=(10, 6))
        plt.plot(mean_predicted_value, fraction_of_positives, 's-', label='Model')
        plt.plot([0, 1], [0, 1], 'k--', label='Perfect calibration')
        plt.xlabel('Mean Predicted Probability', fontsize=12)
        plt.ylabel('Fraction of Positives', fontsize=12)
        plt.title(title, fontsize=14, fontweight='bold')
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(filename, dpi=150, bbox_inches='tight')
        plt.close()
        print(f"  Saved {filename}")
    except Exception as e:
        print(f"  Skipping calibration plot: {e}")


def plot_cv_scores(cv_scores, model_names, filename):
    """Plot cross-validation scores comparison."""
    plt.figure(figsize=(12, 6))
    
    positions = np.arange(len(model_names))
    bp = plt.boxplot([cv_scores[name] for name in model_names], 
                     positions=positions, widths=0.6, patch_artist=True,
                     showmeans=True, meanline=True)
    
    for patch in bp['boxes']:
        patch.set_facecolor('lightblue')
        patch.set_alpha(0.7)
    
    plt.xticks(positions, model_names, rotation=45, ha='right')
    plt.ylabel('Accuracy', fontsize=12)
    plt.title('Cross-Validation Scores (5-Fold)', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig(filename, dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved {filename}")


def evaluate_baselines(X, y, X_train, X_test, y_train, y_test):
    """Evaluate baseline models for comparison."""
    print("\n" + "="*60)
    print("BASELINE MODELS")
    print("="*60)
    
    baselines = {}
    
    # 1. Majority class baseline
    dummy = DummyClassifier(strategy="most_frequent", random_state=RANDOM_STATE)
    dummy.fit(X_train, y_train)
    pred_dummy = dummy.predict(X_test)
    acc_dummy = accuracy_score(y_test, pred_dummy)
    
    cv_dummy = cross_val_score(dummy, X, y, cv=5, scoring='accuracy')
    
    baselines['Majority Class'] = {
        'test_accuracy': float(acc_dummy),
        'cv_mean': float(cv_dummy.mean()),
        'cv_std': float(cv_dummy.std()),
        'description': 'Always predicts the most common class'
    }
    
    print(f"\n1. Majority Class Baseline")
    print(f"   Test Accuracy: {acc_dummy:.4f}")
    print(f"   CV Accuracy: {cv_dummy.mean():.4f} ± {cv_dummy.std():.4f}")
    
    # 2. Single feature baseline (material_type only)
    single_feature_pipe = build_pipeline(
        DecisionTreeClassifier(random_state=RANDOM_STATE),
        features=["material_type"]
    )
    single_feature_pipe.fit(X_train[["material_type"]], y_train)
    pred_single = single_feature_pipe.predict(X_test[["material_type"]])
    acc_single = accuracy_score(y_test, pred_single)
    
    cv_single = cross_val_score(single_feature_pipe, X[["material_type"]], y, cv=5, scoring='accuracy')
    
    baselines['Material Type Only'] = {
        'test_accuracy': float(acc_single),
        'cv_mean': float(cv_single.mean()),
        'cv_std': float(cv_single.std()),
        'description': 'Decision tree using only material_type feature'
    }
    
    print(f"\n2. Material Type Only (Single Feature)")
    print(f"   Test Accuracy: {acc_single:.4f}")
    print(f"   CV Accuracy: {cv_single.mean():.4f} ± {cv_single.std():.4f}")
    
    # 3. Without material_type (to see if other features help)
    other_features = ["wet_or_dry", "texture", "biodegradable"]
    other_pipe = build_pipeline(
        DecisionTreeClassifier(random_state=RANDOM_STATE),
        features=other_features
    )
    other_pipe.fit(X_train[other_features], y_train)
    pred_other = other_pipe.predict(X_test[other_features])
    acc_other = accuracy_score(y_test, pred_other)
    
    cv_other = cross_val_score(other_pipe, X[other_features], y, cv=5, scoring='accuracy')
    
    baselines['Without Material Type'] = {
        'test_accuracy': float(acc_other),
        'cv_mean': float(cv_other.mean()),
        'cv_std': float(cv_other.std()),
        'description': 'Decision tree without material_type (texture, wet/dry, biodegradable only)'
    }
    
    print(f"\n3. Without Material Type (Other Features)")
    print(f"   Test Accuracy: {acc_other:.4f}")
    print(f"   CV Accuracy: {cv_other.mean():.4f} ± {cv_other.std():.4f}")
    
    print(f"\n💡 Insight: Material type contributes ~{(acc_single - acc_other) * 100:.1f}% to accuracy")
    
    return baselines


def main():
    print("="*60)
    print("ADVANCED ML TRAINING & EVALUATION")
    print("="*60)
    
    # Load data
    df = pd.read_csv("dataset/waste_data.csv")
    print(f"\n✓ Loaded {len(df)} rows")
    print(f"  Unique feature combinations: {df[FEATURES].drop_duplicates().shape[0]}")
    print(f"  Classes: {sorted(df[TARGET].unique())}")
    
    X, y = df[FEATURES], df[TARGET]
    
    # Check for duplicates
    dup_count = df[FEATURES + [TARGET]].duplicated().sum()
    if dup_count > 0:
        print(f"  ⚠ Warning: {dup_count} duplicate rows found")
    
    # Train/test split (stratified)
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE, stratify=y
    )
    
    print(f"\n  Train: {len(X_train)} | Test: {len(X_test)}")
    print(f"  Test class distribution:")
    for cls, count in Counter(y_test).most_common():
        print(f"    {cls}: {count}")
    
    # Baselines
    baselines = evaluate_baselines(X, y, X_train, X_test, y_train, y_test)
    
    # Main models
    print("\n" + "="*60)
    print("MAIN MODELS")
    print("="*60)
    
    models = {
        "Decision Tree": DecisionTreeClassifier(
            max_depth=10, min_samples_split=5, random_state=RANDOM_STATE
        ),
        "Random Forest": RandomForestClassifier(
            n_estimators=100, max_depth=15, random_state=RANDOM_STATE, n_jobs=-1
        ),
        "SVM": SVC(
            kernel="rbf", C=10, gamma='scale', probability=True, random_state=RANDOM_STATE
        ),
        "Naive Bayes": MultinomialNB(alpha=1.0),
    }
    
    os.makedirs("models", exist_ok=True)
    os.makedirs("models/plots", exist_ok=True)
    
    labels = sorted(y.unique())
    results = {}
    cv_scores_dict = {}
    
    for name, model in models.items():
        print(f"\n{'='*60}")
        print(f"{name}")
        print(f"{'='*60}")
        
        pipe = build_pipeline(model)
        
        # Train
        pipe.fit(X_train, y_train)
        
        # Predictions
        pred_train = pipe.predict(X_train)
        pred_test = pipe.predict(X_test)
        
        # Probabilities (for calibration)
        try:
            proba_test = pipe.predict_proba(X_test)
        except:
            proba_test = None
        
        # Metrics
        acc_train = accuracy_score(y_train, pred_train)
        acc_test = accuracy_score(y_test, pred_test)
        
        # Cross-validation
        print(f"\n  Running 5-fold cross-validation...")
        cv_scores = cross_val_score(pipe, X, y, cv=5, scoring='accuracy', n_jobs=-1)
        cv_scores_dict[name] = cv_scores
        
        # Confidence interval
        ci_low, ci_high = confidence_interval(acc_test, len(y_test))
        
        # Confusion matrix
        cm = confusion_matrix(y_test, pred_test, labels=labels)
        
        # Per-class metrics
        report = classification_report(y_test, pred_test, output_dict=True, zero_division=0)
        
        metrics = {
            "train_accuracy": float(acc_train),
            "test_accuracy": float(acc_test),
            "cv_mean": float(cv_scores.mean()),
            "cv_std": float(cv_scores.std()),
            "cv_scores": [float(s) for s in cv_scores],
            "ci_95_low": float(ci_low),
            "ci_95_high": float(ci_high),
            "precision": float(precision_score(y_test, pred_test, average="weighted", zero_division=0)),
            "recall": float(recall_score(y_test, pred_test, average="weighted", zero_division=0)),
            "f1": float(f1_score(y_test, pred_test, average="weighted", zero_division=0)),
            "confusion_matrix": cm.tolist(),
            "labels": labels,
            "per_class": report
        }
        
        # Check for overfitting
        overfit = acc_train - acc_test
        if overfit > 0.10:
            metrics['warning'] = f'Possible overfitting (train-test gap: {overfit:.2%})'
        
        results[name] = metrics
        
        # Print summary
        print(f"\n  Train Accuracy:   {acc_train:.4f}")
        print(f"  Test Accuracy:    {acc_test:.4f}")
        print(f"  CV Accuracy:      {cv_scores.mean():.4f} ± {cv_scores.std():.4f}")
        print(f"  95% CI:           [{ci_low:.4f}, {ci_high:.4f}]")
        print(f"  Precision:        {metrics['precision']:.4f}")
        print(f"  Recall:           {metrics['recall']:.4f}")
        print(f"  F1 Score:         {metrics['f1']:.4f}")
        
        if overfit > 0.10:
            print(f"  ⚠ Warning: Train-test gap = {overfit:.2%}")
        
        # Save confusion matrix
        plot_confusion_matrix(
            cm, labels, 
            f'{name} - Confusion Matrix',
            f'models/plots/{name.lower().replace(" ", "_")}_confusion.png'
        )
        
        # Learning curve
        print(f"\n  Generating learning curve...")
        plot_learning_curve(
            pipe, X, y,
            f'{name} - Learning Curve',
            f'models/plots/{name.lower().replace(" ", "_")}_learning_curve.png'
        )
        
        # Feature importance (for tree-based models)
        if name in ["Decision Tree", "Random Forest"]:
            print(f"  Calculating feature importance...")
            # Get feature names after one-hot encoding
            encoder = pipe.named_steps['encode']
            feature_names = encoder.get_feature_names_out()
            
            importance = pipe.named_steps['model'].feature_importances_
            
            # Aggregate by original feature
            feature_groups = {}
            for fname, imp in zip(feature_names, importance):
                orig_feature = fname.split('__')[1] if '__' in fname else fname
                base_feature = orig_feature.split('_')[0]  # Get the feature category
                
                # Map back to original features
                for orig in FEATURES:
                    if orig in fname:
                        feature_groups[orig] = feature_groups.get(orig, 0) + imp
                        break
            
            metrics['feature_importance'] = feature_groups
            
            plot_feature_importance(
                np.array([feature_groups.get(f, 0) for f in FEATURES]),
                FEATURES,
                f'{name} - Feature Importance',
                f'models/plots/{name.lower().replace(" ", "_")}_importance.png'
            )
        
        # Save model
        filename = name.lower().replace(" ", "_") + ".joblib"
        joblib.dump(pipe, os.path.join("models", filename))
        print(f"\n  ✓ Saved models/{filename}")
    
    # Plot CV comparison
    print(f"\n{'='*60}")
    print("GENERATING COMPARISON PLOTS")
    print(f"{'='*60}\n")
    
    plot_cv_scores(cv_scores_dict, list(models.keys()), 
                   'models/plots/cv_comparison.png')
    
    # Overall comparison plot
    plt.figure(figsize=(14, 6))
    
    model_names = list(models.keys())
    test_accs = [results[name]['test_accuracy'] for name in model_names]
    cv_means = [results[name]['cv_mean'] for name in model_names]
    cv_stds = [results[name]['cv_std'] for name in model_names]
    
    x = np.arange(len(model_names))
    width = 0.35
    
    plt.bar(x - width/2, test_accs, width, label='Test Accuracy', color='steelblue', alpha=0.8)
    plt.bar(x + width/2, cv_means, width, label='CV Mean', color='coral', alpha=0.8)
    plt.errorbar(x + width/2, cv_means, yerr=cv_stds, fmt='none', color='black', capsize=5)
    
    plt.xlabel('Model', fontsize=12)
    plt.ylabel('Accuracy', fontsize=12)
    plt.title('Model Performance Comparison', fontsize=14, fontweight='bold')
    plt.xticks(x, model_names, rotation=45, ha='right')
    plt.legend()
    plt.grid(True, alpha=0.3, axis='y')
    plt.tight_layout()
    plt.savefig('models/plots/model_comparison.png', dpi=150, bbox_inches='tight')
    plt.close()
    print(f"  Saved models/plots/model_comparison.png")
    
    # Save results
    with open("models/model_comparison.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ Saved models/model_comparison.json")
    
    # Save comprehensive report
    report = {
        'dataset_info': {
            'total_samples': len(df),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
            'n_features': len(FEATURES),
            'features': FEATURES,
            'n_classes': len(labels),
            'classes': labels,
            'duplicate_rows': int(dup_count)
        },
        'baselines': baselines,
        'models': results
    }
    
    with open("models/evaluation_report.json", "w") as f:
        json.dump(report, f, indent=2)
    print(f"✓ Saved models/evaluation_report.json")
    
    # Final summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    
    print(f"\n📊 Baselines:")
    for name, metrics in baselines.items():
        print(f"  {name:25} Test: {metrics['test_accuracy']:.4f}  CV: {metrics['cv_mean']:.4f} ± {metrics['cv_std']:.4f}")
    
    print(f"\n🤖 Main Models:")
    for name in model_names:
        m = results[name]
        print(f"  {name:25} Test: {m['test_accuracy']:.4f}  CV: {m['cv_mean']:.4f} ± {m['cv_std']:.4f}")
    
    # Best model
    best_model = max(model_names, key=lambda n: results[n]['cv_mean'])
    print(f"\n🏆 Best Model (by CV): {best_model}")
    print(f"   CV Accuracy: {results[best_model]['cv_mean']:.4f} ± {results[best_model]['cv_std']:.4f}")
    
    print(f"\n✅ Training complete! Check models/plots/ for visualizations.")


if __name__ == "__main__":
    main()
