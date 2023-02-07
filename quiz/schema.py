import graphene
import logging
from graphene_django import DjangoObjectType
from .models import Category, Question, Answer, Quizzes
from graphql import GraphQLError
from django.contrib.auth.decorators import permission_required


class CategoryType(DjangoObjectType):
    class Meta:
        model = Category
        fields = ["id", "name"]


class QuizzesType(DjangoObjectType):
    class Meta:
        model = Quizzes
        fields = ["id", "title", "category", "created_on"]


class QuestionType(DjangoObjectType):
    class Meta:
        model = Question
        fields = ["id", "quiz", "title", "created_on", "is_active"]


class AnswerType(DjangoObjectType):
    class Meta:
        model = Answer
        fields = ["id", "question", "answer_text", "is_right"]


class Query(graphene.ObjectType):
    all_category = graphene.List(CategoryType)
    category = graphene.Field(CategoryType, category_id=graphene.Int())

    all_quizzes = graphene.List(QuizzesType)
    quiz = graphene.Field(QuizzesType, quiz_id=graphene.Int())

    all_questions = graphene.List(QuestionType)

    questions = graphene.Field(QuestionType, question_id=graphene.Int())
    all_answers = graphene.List(AnswerType, question_id=graphene.Int())

    def resolve_all_category(root, info):
        return Category.objects.all()

    def resolve_category(root, info, category_id):
        return Category.objects.get(pk=category_id)

    def resolve_all_quizzes(root, info):
        return Quizzes.objects.all()

    def resolve_quiz(root, info, quiz_id):
        return Quizzes.objects.get(pk=quiz_id)

    def resolve_all_questions(root, info):
        return Question.objects.all()

    def resolve_questions(root, info, question_id):
        return Question.objects.get(pk=question_id)

    def resolve_all_answers(root, info, question_id):
        return Answer.objects.filter(question=question_id)


class AddCategoryMutation(graphene.Mutation):

    class Arguments:
        name = graphene.String(required=True)

    category = graphene.Field(CategoryType)

    @permission_required('auth.view_user')
    @classmethod
    def mutate(cls, root, info, name):
        category = Category(name=name)
        category.save()
        return AddCategoryMutation(category=category)


class UpdateCategoryMutation(graphene.Mutation):
    class Arguments:
        category_id = graphene.ID()
        name = graphene.String(required=True)

    category = graphene.Field(CategoryType)

    @classmethod
    def mutate(cls, root, info, name, category_id):
        category = Category.objects.get(id=category_id)
        category.name = name
        category.save()
        return UpdateCategoryMutation(category=category)


class DeleteCategoryMutation(graphene.Mutation):
    class Arguments:
        category_id = graphene.ID()

    category = graphene.Field(CategoryType)

    @classmethod
    def mutate(cls, root, info, category_id):
        category = Category.objects.get(id=category_id)
        category.delete()
        return


class QuizInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    category_id = graphene.Int(required=True)

    def clean(self, quiz_id):
        is_quiz_empty = Question.objects.filter(quiz_id=quiz_id)
        if is_quiz_empty:
            raise GraphQLError('Quiz is not empty, you can not update the quiz')


class AddQuizMutation(graphene.Mutation):
    class Arguments:
        quizData = QuizInput()

    quiz = graphene.Field(QuizzesType)

    @classmethod
    def mutate(cls, root, info, quizData):
        quiz = Quizzes.objects.create(**quizData)
        print("quiz", quiz)
        return AddQuizMutation(quiz=quiz)


class UpdateQuizMutation(graphene.Mutation):
    class Arguments:
        quiz_id = graphene.ID()
        quizData = QuizInput()

    quiz = graphene.Field(QuizzesType)

    @classmethod
    def mutate(cls, root, info, quizData, quiz_id):
        quizData.clean(quiz_id)
        quiz = Quizzes.objects.get(id=quiz_id)
        quiz.title = quizData.title
        quiz.category_id = quizData.category_id
        quiz.save()
        return UpdateQuizMutation(quiz=quiz)


class DeleteQuizMutation(graphene.Mutation):
    class Arguments:
        quiz_id = graphene.ID()

    quiz = graphene.Field(QuizzesType)

    @classmethod
    def mutate(cls, root, info, quiz_id):
        quiz = Quizzes.objects.get(id=quiz_id)
        quiz.delete()
        return


class QuestionInput(graphene.InputObjectType):
    title = graphene.String(required=True)
    is_active = graphene.Boolean()
    quiz_id = graphene.Int(required=True)

    def clean(self):
        title = self.title

        existing = Question.objects.filter(title=title).first()
        if existing:
            raise GraphQLError("Question is already exists")


class AddQuestionMutation(graphene.Mutation):
    class Arguments:
        questionData = QuestionInput()

    question = graphene.Field(QuestionType)

    @classmethod
    def mutate(cls, root, info, questionData):
        questionData.clean()
        question = Question.objects.create(**questionData)
        return AddQuestionMutation(question=question)


class UpdateQuestionMutation(graphene.Mutation):
    class Arguments:
        question_id = graphene.ID()
        question = QuestionInput()

    question = graphene.Field(QuestionType)

    @classmethod
    def mutate(cls, root, info, question_id, questionData):
        question = Question.objects.get(id=question_id)
        question.title = questionData.title
        question.quiz_id = questionData.quiz_id
        question.is_active = questionData.is_active
        question.save()
        return UpdateQuestionMutation(question=question)


class DeleteQuestionMutation(graphene.Mutation):
    class Arguments:
        question_id = graphene.ID()

    quiz = graphene.Field(QuestionType)

    @classmethod
    def mutate(cls, root, info, question_id):
        quiz = Question.objects.get(id=question_id)
        quiz.delete()
        return


class AnswerInput(graphene.InputObjectType):
    question_id = graphene.ID()
    answer_text = graphene.String()
    is_right = graphene.Boolean()

    def clean(self):
        answer_text = self.answer_text
        question_id = self.question_id
        is_right = self.is_right

        existing = Answer.objects.filter(question_id=question_id, answer_text=answer_text)
        if existing:
            raise GraphQLError("Answer is already exists for the same question")

        if is_right:
            right_answer_exist = Answer.objects.filter(question_id=question_id, is_right=True)
            if right_answer_exist:
                raise GraphQLError("One question has only one right answer")


class AddAnswerMutation(graphene.Mutation):
    class Arguments:
        answer_data = AnswerInput()

    answer = graphene.Field(AnswerType)


    @classmethod
    def mutate(cls, root, info, answer_data):
        answer_data.clean()
        answer = Answer.objects.create(**answer_data)
        return AddAnswerMutation(answer=answer)


class DeleteAnswerMutation(graphene.Mutation):
    class Arguments:
        answer_id = graphene.ID()

    quiz = graphene.Field(AnswerType)

    @classmethod
    def mutate(cls, root, info, answer_id):
        quiz = Answer.objects.get(id=answer_id)
        quiz.delete()
        return


class Mutation(graphene.ObjectType):
    add_category = AddCategoryMutation.Field()
    update_category = UpdateCategoryMutation.Field()
    delete_category = DeleteCategoryMutation.Field()

    add_quiz = AddQuizMutation.Field()
    update_quiz = UpdateQuizMutation.Field()
    delete_quiz = DeleteQuizMutation.Field()

    add_question = AddQuestionMutation.Field()
    update_question = UpdateQuestionMutation.Field()
    delete_question = DeleteQuestionMutation.Field()

    add_answer = AddAnswerMutation.Field()
    delete_answer = DeleteAnswerMutation.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
